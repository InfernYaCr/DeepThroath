# Eval — Руководство разработчика

## Архитектура

```
eval/
├── eval_rag_metrics.py      # Основной pipeline оценки
├── config/
│   ├── targets.yaml         # Конфигурация судей (модели)
│   └── eval_config.yaml     # Параметры запуска по умолчанию
├── scripts/
│   └── run_eval.py          # CLI точка входа
├── results/                 # Папки прогонов (создаются автоматически)
│   └── {ts}_{stem}/
│       ├── metrics.json     # Детальные результаты
│       ├── metrics.csv      # То же в табличном виде
│       ├── report.md        # Читаемый отчёт
│       └── checkpoint.json  # Временный (удаляется по завершении)
├── docs/
│   ├── DEVELOPMENT.md       # Этот файл
│   └── TESTING.md           # Руководство по тестированию
└── requirements.txt
```

### Основные компоненты

| Компонент | Файл | Назначение |
|---|---|---|
| Судьи | `eval_rag_metrics.py` | `OpenRouterJudge`, `GigaChatJudge`, OpenAI string |
| Pipeline | `eval_rag_metrics.py` | `main()`, `run_eval()`, `evaluate_record()` |
| CLI | `scripts/run_eval.py` | Разбор аргументов, загрузка конфигов |
| Чекпоинты | `eval_rag_metrics.py` | `load_checkpoint()`, `save_checkpoint()` |
| Отчёты | `eval_rag_metrics.py` | `generate_report()` |

### Поток данных

```
Input JSON → ThreadPoolExecutor → evaluate_record() → metrics.json + report.md
                                        ↓
                               judge.generate(prompt)
                                        ↓
                               AnswerRelevancyMetric / FaithfulnessMetric
```

### Параллелизм и thread-safety

Каждый воркер создаёт **собственные** экземпляры судьи и метрик DeepEval — это требование библиотеки, которая не является thread-safe при разделении объектов между потоками. Чекпоинт защищён `threading.Lock`.

## Добавление новой модели-судьи

### 1. Добавить в `eval/config/targets.yaml`

```yaml
targets:
  - name: my-new-judge
    provider: openrouter          # openrouter | gigachat | openai
    model: anthropic/claude-3-haiku
    description: "Claude Haiku — быстрый и дешёвый"
    threshold: 0.7
```

### 2. Для нового провайдера — реализовать класс судьи в `eval_rag_metrics.py`

Судья должен наследоваться от `DeepEvalBaseLLM`:

```python
class MyProviderJudge(DeepEvalBaseLLM):
    def __init__(self, model: str):
        self.model = model

    def get_model_name(self) -> str:
        return self.model

    def load_model(self):
        # Возвращает клиент (или self)
        return self

    def generate(self, prompt: str) -> str:
        # Синхронный вызов API
        ...

    async def a_generate(self, prompt: str) -> str:
        return await asyncio.get_event_loop().run_in_executor(
            None, self.generate, prompt
        )
```

### 3. Зарегистрировать в `build_judge()`

```python
def build_judge(verbose: bool = False):
    if JUDGE_PROVIDER == "myprovider":
        return MyProviderJudge(model=JUDGE_MODEL_NAME)
    ...
```

## Справочник по конфигурации

### `eval/config/targets.yaml`

| Поле | Тип | Описание |
|---|---|---|
| `name` | str | Уникальный идентификатор (используется в `--judge`) |
| `provider` | str | `openrouter`, `gigachat`, или `openai` |
| `model` | str | Название модели в формате провайдера |
| `description` | str | Человекочитаемое описание |
| `threshold` | float | Порог pass/fail (0.0–1.0) |

### `eval/config/eval_config.yaml`

| Поле | Тип | По умолчанию | Описание |
|---|---|---|---|
| `max_workers` | int | 10 | Параллельных потоков |
| `default_judge` | str | `gpt4o-mini-or` | Судья по умолчанию (имя из targets.yaml) |
| `metrics.answer_relevancy` | bool | true | Считать AR |
| `metrics.faithfulness` | bool | true | Считать Faithfulness (при наличии контекста) |
| `output_dir` | str | `results` | Папка для результатов |

## Переменные окружения

Копируйте `.env.example` в `.env` и заполните нужные ключи:

```bash
JUDGE_PROVIDER=openrouter
JUDGE_MODEL=openai/gpt-4o-mini
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
GIGACHAT_CREDENTIALS=...
```

При использовании `run_eval.py` провайдер и модель берутся из `targets.yaml`, не из `.env`.

## Структура входного JSON

```json
[
  {
    "session_id": "unique-id",
    "category": "faq",
    "intent": "information",
    "user_query": "Что такое RAG?",
    "actual_answer": "RAG — метод генерации с извлечением...",
    "expected_answer": "Retrieval-Augmented Generation...",
    "retrieval_context": ["Чанк 1...", "Чанк 2..."]
  }
]
```

`retrieval_context` необязателен. При его отсутствии Faithfulness не считается.

## Программный запуск (из Python)

```python
from eval.eval_rag_metrics import run_eval

run_eval(
    input_path="data/questions.json",
    judge_config={
        "provider": "openrouter",
        "model": "openai/gpt-4o-mini",
        "name": "gpt4o-mini-or",
    },
    max_workers=5,
    threshold=0.7,
)
```
