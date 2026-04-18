# RAGAS Evaluation Pipeline — Руководство

## Содержание

1. [Быстрый старт](#быстрый-старт)
2. [Архитектура пайплайна](#архитектура-пайплайна)
3. [Основные модули](#основные-модули)
4. [Два режима запуска](#два-режима-запуска)
5. [Конфигурация](#конфигурация)
6. [Переменные окружения и нюансы](#переменные-окружения-и-нюансы)
7. [Метрики](#метрики)
8. [Кастомные метрики](#кастомные-метрики)
9. [Судьи (targets.yaml)](#судьи-targetsyaml)
10. [Выходные файлы](#выходные-файлы)
11. [Типичные ошибки](#типичные-ошибки)
12. [Зависимости](#зависимости)

---

## Быстрый старт

```bash
# из корня проекта

# Режим 1: папка прогона DeepEval (без вызова RAG API)
.venv/bin/python3 eval/eval_ragas_metrics.py eval/results/<папка_прогона>/

# Режим 2: исходный датасет JSON (вызывает RAG API для каждой записи)
.venv/bin/python3 eval/eval_ragas_metrics.py eval/datasets/<file>.json

# Тестовый прогон — только 1 запись (для отладки)
.venv/bin/python3 eval/eval_ragas_metrics.py eval/results/<папка_прогона>/ --limit 1
```

---

## Архитектура пайплайна

```
Input (DeepEval run folder или dataset JSON)
        │
        ▼
┌─────────────────────────────────────────────────────────────────────┐
│  eval_ragas_metrics.py — основной пайплайн                          │
│                                                                      │
│  1. load_from_deepeval_run() / load_and_enrich_records()            │
│     Загружает records: [{user_query, actual_answer,                  │
│                          retrieval_context, expected_answer}]        │
│                                                                      │
│  2. _filter_records()                                                │
│     Убирает записи без user_query или actual_answer                  │
│                                                                      │
│  3. build_judge() → InstructorLLM (AsyncOpenAI)                      │
│     Строит LLM-судью через ragas.llms.llm_factory                   │
│                                                                      │
│  4. build_embeddings() → RagasOpenAIEmbeddings | None                │
│     Строит embeddings (только если есть OPENAI_API_KEY)              │
│                                                                      │
│  5. build_builtin_metrics() → [Faithfulness, CP, CR, AC, AR]        │
│     Graceful-skip: метрики без нужных данных не включаются           │
│                                                                      │
│  6. discover_custom_metrics() → [ExampleCustomMetric, ...]           │
│     Автодискавери всех MetricWithLLM+SingleTurnMetric из             │
│     eval/custom_metrics/*.py                                         │
│                                                                      │
│  7. _score_builtin_metric(metric, records)                           │
│     metric.abatch_score([{user_input, response, ...}])               │
│     ← RAGAS 0.4.3 API (не evaluate())                                │
│                                                                      │
│  8. _score_custom_metrics(custom_metrics, records)                   │
│     metric._single_turn_ascore(SingleTurnSample)                     │
│     ← старый RAGAS API (MetricWithLLM)                               │
│                                                                      │
│  9. save_results(records, all_scores, run_dir)                       │
│     metrics.json с явным null для всех стандартных ключей            │
└─────────────────────────────────────────────────────────────────────┘
        │
        ▼
eval/results/{timestamp}_{stem}_ragas/metrics.json
        │
        ▼
Next.js /api/eval/ragas → /eval (вкладка RAGAS)
```

### Почему два пути скоринга

RAGAS 0.4.3 полностью переписал архитектуру метрик. Появились **две несовместимые иерархии**:

| | Встроенные (`ragas.metrics.collections`) | Кастомные (`ragas.metrics.base`) |
|---|---|---|
| Базовый класс | `BaseMetric` | `MetricWithLLM + SingleTurnMetric` |
| Метод оценки | `abatch_score([dict, ...])` | `_single_turn_ascore(SingleTurnSample)` |
| Совместим с `evaluate()`? | ❌ Нет | ✓ Да |
| LLM передаётся | при `__init__` | через `evaluate()` / вручную |

`ragas.evaluation.evaluate()` проверяет `isinstance(m, Metric)` — но `Faithfulness` наследует `BaseMetric`, а не `Metric` → всегда `False` → **evaluate() принципиально несовместима с новыми метриками**. Решение: вызываем `abatch_score()` напрямую.

---

## Основные модули

### `build_judge(provider, model)` → `InstructorLLM`

Создаёт LLM-судью. Ключевые детали:

- Использует `AsyncOpenAI` (не `OpenAI`) — `abatch_score` вызывает `agenerate()` и требует async-клиент
- Передаёт `max_tokens=4096` — дефолт InstructorLLM (1024) слишком мал для Faithfulness (генерирует длинные списки утверждений → truncation → null scores)
- Для reasoning-моделей (Qwen3, QwQ, DeepSeek-R1) добавляет `extra_body={"reasoning": {"effort": "none"}}` — thinking-режим ломает PydanticPrompt JSON-парсинг

```python
_OPENROUTER_REASONING_PREFIXES = (
    "qwen/qwen3", "qwen/qwq", "deepseek/deepseek-r", "openai/o1", ...
)
```

---

### `build_embeddings()` → `RagasOpenAIEmbeddings | None`

Строит embeddings для `AnswerRelevancy` и `AnswerCorrectness`.

- Требует `OPENAI_API_KEY` — OpenRouter **не поддерживает** embedding API
- Если ключа нет → возвращает `None` → оба метрики автоматически пропускаются

---

### `build_builtin_metrics(llm, has_context, has_reference, embeddings)` → `list[BaseMetric]`

Graceful-skip логика:

| Метрика | Пропускается если |
|---------|------------------|
| `AnswerRelevancy` | нет embeddings |
| `Faithfulness` | нет retrieved_contexts |
| `ContextPrecision` | нет contexts ИЛИ нет reference |
| `ContextRecall` | нет contexts ИЛИ нет reference |
| `AnswerCorrectness` | нет reference; без embeddings — `weights=[1.0, 0.0]` |

---

### `_score_builtin_metric(metric, records)` → `list[float | None]`

Инспектирует сигнатуру `metric.ascore()` и передаёт **только те поля**, которые метрика ожидает:

```python
allowed_params = set(inspect.signature(metric.ascore).parameters) - {"self"}
# Faithfulness:        {user_input, response, retrieved_contexts}
# ContextPrecision:    {user_input, reference, retrieved_contexts}
# ContextRecall:       {user_input, retrieved_contexts, reference}
# AnswerCorrectness:   {user_input, response, reference}
# AnswerRelevancy:     {user_input, response}
```

Передача лишних полей вызывает `TypeError: unexpected keyword argument` — именно это ломало пайплайн.

---

### `discover_custom_metrics()` → `list[MetricWithLLM]`

Сканирует `eval/custom_metrics/*.py` через `pkgutil.iter_modules`, инстанцирует все классы, удовлетворяющие:
```python
issubclass(cls, MetricWithLLM) and issubclass(cls, SingleTurnMetric)
```

LLM инжектируется в найденные инстансы автоматически в `run_pipeline()`.

---

### `save_results(records, all_scores, run_dir)` → `Path`

Ключевой нюанс: **всегда записывает все 5 стандартных `*_score` ключей**, даже если метрика была пропущена:

```python
for out_key in BUILTIN_MAP.values():
    row[out_key] = None   # явный null, не отсутствующий ключ
```

Без этого фронт получает `undefined` вместо `null`, что проходит все null-проверки в JS и приводит к `NaN%` в KPI-карточках.

---

## Два режима запуска

### Режим 1 — Папка прогона DeepEval (рекомендуется)

Передаётся **директория** `eval/results/<папка>/`.

- Читает `api_responses.json` → берёт `question`, `answer`, `retrieved_chunks[].content`
- Читает `metrics.json` → берёт `expected_answer` (join по id)
- **RAG API не вызывается** — все данные уже в папке прогона

```bash
.venv/bin/python3 eval/eval_ragas_metrics.py \
  eval/results/20260414_121501_20260329_173829_exp_top_k_10_dataset/
```

Структура папки прогона DeepEval:
```
eval/results/<timestamp>_<stem>/
├── api_responses.json   ← вопросы + ответы API + retrieved_chunks
├── metrics.json         ← expected_answer + deepeval-метрики
├── metrics.csv
└── report.md
```

### Режим 2 — Исходный датасет JSON

Передаётся **файл** `eval/datasets/<file>.json`.

- Для каждой записи вызывает RAG API (настройка через `eval_config.yaml` → секция `api`)
- Получает `actual_answer` и `retrieval_context` из ответа API

```bash
.venv/bin/python3 eval/eval_ragas_metrics.py \
  eval/datasets/20260329_173829_exp_top_k_10_dataset.json
```

---

## Конфигурация

### eval/config/eval_config.yaml

```yaml
max_workers: 3               # параллельных потоков к судье (снизить до 1-2 при 429)
default_judge: gpt4o-mini-or # имя судьи из targets.yaml
metrics:
  answer_relevancy: true
  faithfulness: true
output_dir: results
```

**`default_judge`** — ключевое поле. Скрипт ищет судью по имени в `targets.yaml`.

### eval/config/targets.yaml

Реестр судей. Каждый судья:

```yaml
targets:
  - name: gpt4o-mini-or         # имя для default_judge
    provider: openrouter         # openrouter | openai | gigachat
    model: openai/gpt-4o-mini    # модель у провайдера
    description: "GPT-4o-mini — быстрый"
    threshold: 0.7
```

Доступные судьи:

| name | provider | model | заметка |
|------|----------|-------|---------|
| `gpt4o-mini-or` | openrouter | openai/gpt-4o-mini | ✅ рекомендуется — быстрый, надёжный JSON |
| `gpt4o-or` | openrouter | openai/gpt-4o | точный |
| `qwen-235b-or` | openrouter | qwen/qwen3-235b-a22b | max качество, reasoning отключается авто |
| `qwen-72b-or` | openrouter | qwen/qwen-2.5-72b-instruct | качество/цена |
| `qwq-32b-or` | openrouter | qwen/qwq-32b | reasoning-судья |
| `gemini-flash` | openrouter | google/gemini-flash-1.5 | дешёвый |
| `gigachat` | gigachat | GigaChat-Pro | российская модель |

---

## Переменные окружения и нюансы

### eval/.env (НЕ коммитить)

```bash
# Обязательно для судьи через OpenRouter (большинство таргетов)
OPENROUTER_API_KEY=sk-or-...

# Нужен для AnswerRelevancy и AnswerCorrectness (embeddings)
# Без него эти метрики автоматически пропускаются
OPENAI_API_KEY=sk-...

# Опционально: кастомный base_url для OpenAI-совместимых эндпоинтов
# OPENAI_BASE_URL=https://...

# Опционально: fallback URL API (только режим 2, если api не задан в eval_config.yaml)
# API_URL=http://localhost:8000/api/ask
```

### ⚠️ Нюанс: OPENAI_API_KEY vs OPENROUTER_API_KEY

RAGAS использует **два отдельных AI-сервиса**:

```
┌──────────────────────────────────┬──────────────────────────────────┐
│ LLM-судья                        │ Embeddings (AnswerRelevancy,      │
│ qwen/gpt-4o/etc.                 │ AnswerCorrectness)                │
│ ключ: OPENROUTER_API_KEY         │ model: text-embedding-3-small     │
│ провайдер: OpenRouter            │ ключ: OPENAI_API_KEY              │
│                                  │ провайдер: только OpenAI напрямую │
└──────────────────────────────────┴──────────────────────────────────┘
```

**Итог:**
- Только `OPENROUTER_API_KEY` → работают Faithfulness, ContextPrecision, ContextRecall + кастомные. AnswerRelevancy и AnswerCorrectness (полный) **пропускаются**
- `OPENROUTER_API_KEY` + `OPENAI_API_KEY` → работают все 5 метрик
- OpenRouter **не поддерживает** embedding-запросы стандарта OpenAI

### ⚠️ Нюанс: reasoning-модели (Qwen3, DeepSeek-R1)

Reasoning-модели в режиме thinking генерируют служебные токены, после чего возвращают некорректный JSON (например `"{"` или голое число `0.75`). RAGAS PydanticPrompt не может распарсить такой вывод → все встроенные метрики возвращают `null`.

**Пайплайн автоматически** отключает thinking для таких моделей через:
```python
extra_body={"reasoning": {"effort": "none"}}
```

Список моделей с автоматическим отключением: `qwen/qwen3*`, `qwen/qwq*`, `deepseek/deepseek-r*`, `openai/o1*`, `openai/o3*`, `openai/o4*`.

Если добавляешь новую reasoning-модель — дополни `_OPENROUTER_REASONING_PREFIXES` в `eval_ragas_metrics.py`.

### ⚠️ Нюанс: max_tokens для Faithfulness

Faithfulness внутри разбивает ответ на утверждения и проверяет каждое по контексту. При большом ответе список утверждений может превысить лимит токенов судьи.

Дефолт InstructorLLM = **1024 токена** — этого недостаточно. Пайплайн принудительно устанавливает **4096**.

Если судья возвращает `null` только по Faithfulness — увеличь `max_tokens` через константу `_RAGAS_MAX_TOKENS` в `eval_ragas_metrics.py`.

### Приоритет разрешения судьи

```
eval_config.yaml (default_judge)
        ↓ поиск по имени в
targets.yaml
        ↓ если не найден
.env (JUDGE_PROVIDER + JUDGE_MODEL)
```

---

## Метрики

| Метрика | Нужно | Graceful-skip если |
|---------|-------|--------------------|
| `Faithfulness` | `retrieved_contexts` | нет контекста |
| `AnswerRelevancy` | `OPENAI_API_KEY` + embeddings | нет OPENAI_API_KEY |
| `ContextPrecision` | `retrieved_contexts` + `reference` | нет контекста ИЛИ эталона |
| `ContextRecall` | `retrieved_contexts` + `reference` | нет контекста ИЛИ эталона |
| `AnswerCorrectness` | `reference` | нет эталона; без embeddings — только factual-компонент |

**Маппинг полей датасета → RAGAS:**

| Поле датасета | Поле RAGAS | Примечание |
|---|---|---|
| `user_query` | `user_input` | обязательно |
| `actual_answer` | `response` | обязательно |
| `retrieval_context` (list) | `retrieved_contexts` | нужен для Faithfulness и Context-метрик |
| `expected_answer` | `reference` | нужен для ContextPrecision/Recall, AnswerCorrectness |

---

## Кастомные метрики

### Создание новой метрики

Скопируй `eval/custom_metrics/example_metric.py`, переименуй класс и метрику:

```python
# eval/custom_metrics/my_metric.py
from dataclasses import dataclass, field
from pydantic import BaseModel
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics.base import MetricWithLLM, SingleTurnMetric
from ragas.prompt import PydanticPrompt


class MyInput(BaseModel):          # ← ОБЯЗАТЕЛЬНО Pydantic, не dict
    question: str
    answer: str

class MyOutput(BaseModel):
    score: float
    reason: str

class MyPrompt(PydanticPrompt[MyInput, MyOutput]):
    instruction = "Оцени ... Верни score от 0.0 до 1.0."
    input_model = MyInput
    output_model = MyOutput

@dataclass
class MyMetric(MetricWithLLM, SingleTurnMetric):
    name: str = "my_metric"
    prompt: MyPrompt = field(default_factory=MyPrompt)

    async def _single_turn_ascore(self, sample: SingleTurnSample, callbacks=None) -> float:
        out = await self.prompt.generate(
            data=MyInput(question=sample.user_input or "", answer=sample.response or ""),
            llm=self.llm,
        )
        return max(0.0, min(1.0, float(out.score)))
```

### ⚠️ Важно: `input_model` должен быть Pydantic-моделью

В RAGAS 0.4.x `PydanticPrompt` вызывает `.model_dump_json()` на входном объекте. Если передать `input_model = dict` (как в старых примерах) — будет `AttributeError: 'dict' object has no attribute 'model_dump_json'`.

### Автодискавери

Пайплайн автоматически находит все классы из `eval/custom_metrics/*.py`, удовлетворяющие:
```python
issubclass(cls, MetricWithLLM) and issubclass(cls, SingleTurnMetric)
```
Файлы с именем начинающимся на `_` (например `_base.py`) игнорируются.

### Добавление в реестр фронта

Чтобы кастомная метрика отображалась красиво в UI — добавь запись в `METRIC_META` в `web/src/components/EvalRagasTab.tsx`:

```ts
resort_tone_score: {
    label:       "Resort Tone",
    description: "Тон 5★ курорта: тепло, профессионально, без канцелярщины",
    icon:        Star,
    color:       "yellow",
    hexColor:    "#ca8a04",
},
```

Без записи в реестре метрика всё равно появится в UI — с generic-иконкой и надписью "Кастомная метрика".

---

## Судьи (targets.yaml)

### Добавление нового судьи

```yaml
targets:
  - name: my-judge              # уникальное имя → используй в default_judge
    provider: openrouter         # openrouter | openai | gigachat
    model: openai/gpt-4.1-mini   # модель у провайдера
    description: "Мой судья"
    threshold: 0.7
    # no_reasoning: true         # опциональный флаг (пока не используется пайплайном)
```

После добавления — измени `default_judge` в `eval_config.yaml`.

---

## Выходные файлы

Результаты сохраняются в `eval/results/{timestamp}_{stem}_ragas/`:

```
eval/results/20260418_185232_..._ragas/
└── metrics.json    ← оценки по каждой записи
```

Формат `metrics.json`:

```json
[
  {
    "session_id": "TC-001",
    "category": "kids_complex",
    "intent": null,
    "user_query": "Что такое Лес чудес?",
    "actual_answer": "«Лес чудес» — детский досуговый центр...",
    "expected_answer": "Лес чудес — двухэтажное игровое пространство...",
    "retrieval_context": ["## Основная информация...", "..."],
    "faithfulness_score": 0.923,
    "answer_relevancy_score": null,
    "context_precision_score": 0.653,
    "context_recall_score": 1.0,
    "answer_correctness_score": 0.105,
    "completeness_score": 1.0,
    "resort_tone_score": 0.7
  }
]
```

`null` = метрика была пропущена (нет данных, нет ключа, или LLM вернул некорректный вывод).

Все 5 стандартных `*_score` ключей **всегда присутствуют** в записи (даже как `null`) — это важно для корректного отображения на фронте.

---

## Типичные ошибки

### Все встроенные метрики `null`, reasoning-модель в логах

**Причина:** судья — Qwen3/DeepSeek-R1 без отключённого thinking. PydanticPrompt получает `"{"` вместо JSON.

**Решение:** переключи судью на не-reasoning модель (`gpt4o-mini-or`) или убедись что модель присутствует в `_OPENROUTER_REASONING_PREFIXES`.

---

### `faithfulness_score: null`, остальные считаются

**Причина:** truncation — `max_tokens` слишком мал для длинных ответов. В логах: `"The output is incomplete due to a max_tokens length limit"`.

**Решение:** увеличь `_RAGAS_MAX_TOKENS` в `eval_ragas_metrics.py` (дефолт 4096, попробуй 8192).

---

### `AuthenticationError 401` при запуске

**Причина:** `AnswerRelevancy` пытается вызвать OpenAI Embeddings, а `OPENAI_API_KEY` не задан.

**Решение:**
- Добавь `OPENAI_API_KEY` в `eval/.env` — будут считаться все 5 метрик
- ИЛИ игнорируй — метрика пропускается, остальные считаются

---

### `ModuleNotFoundError: No module named 'ragas'`

```bash
# использовать python из .venv, не системный pip
.venv/bin/python3 -m pip install ragas
```

---

### `429 Too Many Requests`

Уменьши `max_workers` в `eval/config/eval_config.yaml`:
```yaml
max_workers: 1
```

---

### `AttributeError: 'dict' object has no attribute 'model_dump_json'`

**Причина:** кастомная метрика использует `input_model = dict` (старый API).

**Решение:** замени `dict` на Pydantic-модель (см. пример в [Кастомные метрики](#кастомные-метрики)).

---

### `NaN%` в KPI-карточках на фронте

**Причина:** в старых прогонах (до фикса) `answer_relevancy_score` отсутствовал как ключ → JS читал `undefined` → `avg()` считал некорректно.

**Решение:** перезапусти пайплайн — новый `save_results()` всегда пишет явный `null` для всех стандартных ключей.

---

### Результаты сохранились, но все `null`

**Причина:** записи не прошли фильтр — пустые `user_query` или `actual_answer`.

**Проверь:**
```bash
python3 -c "
import json
d = json.load(open('eval/results/<папка>/api_responses.json'))
print([(r.get('question','?'), bool(r.get('answer'))) for r in d[:3]])
"
```

---

## Зависимости

```
ragas>=0.4.3
openai>=1.0
```

Установка (из корня проекта):
```bash
.venv/bin/python3 -m pip install ragas openai
```

> `langchain-openai` / `langchain-core` — в RAGAS 0.4.x **больше не нужны**. Пайплайн использует `ragas.llms.llm_factory` + `AsyncOpenAI` напрямую.
