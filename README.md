# DeepThroath v2 — LLM Red Teaming + RAG Quality Platform

Платформа для тестирования и оценки качества LLM-систем. Объединяет два независимых модуля:

- **Red Team** — автоматические атаки на LLM-ботов по стандарту OWASP LLM Top 10
- **RAG Eval** — оценка качества ответов RAG-системы через LLM-судью (4 метрики DeepEval)

Веб-дашборд на Next.js 15 + тёмный интерфейс.

---

## Структура проекта

```
├── web/                        Next.js дашборд (TypeScript)
│   └── src/app/
│       ├── page.tsx            Вкладка Security
│       ├── eval/page.tsx       Вкладка RAG Eval
│       └── api/                REST API для обеих вкладок
│
├── eval/                       RAG eval pipeline (Python)
│   ├── eval_rag_metrics.py     Основной pipeline (AR, FA, CP, CR)
│   ├── scripts/
│   │   ├── run_eval.py         CLI-запуск прогона
│   │   └── convert_dataset.py  Конвертер top_k → dataset
│   ├── datasets/               Датасеты вопросов
│   ├── config/
│   │   ├── eval_config.yaml    Настройки (workers, судья)
│   │   └── targets.yaml        Доступные LLM-судьи
│   └── results/                Результаты прогонов (генерируется)
│
├── tests/
│   └── eval/                   DeepEval pytest-тесты через живой API
│       ├── conftest.py         Фикстуры, кеш API-ответов
│       └── test_rag_deepeval.py 4 метрики + edge cases
│
├── src/                        Red team модуль (Python)
│   ├── red_team/               Атаки, судья, runner
│   ├── dashboard/              Streamlit-версия (legacy)
│   └── reports/                Генератор PDF/MD отчётов
│
├── scripts/
│   └── run_redteam.py          CLI-запуск red team скана
├── config/
│   ├── attack_config.yaml      Атаки, OWASP-категории, судья
│   └── targets.yaml            Целевые модели
└── results/                    Parquet-файлы сканов
```

---

## Быстрый старт

### 1. Зависимости

```bash
# Единое Python-окружение для Red Team и RAG Eval
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

> **Примечание (Миграция):** Если у вас раньше была папка `eval/.venv` — смело удаляйте её. Теперь используется только единое окружение в корневой папке `.venv`.

# Веб-дашборд
cd web && npm install && cd ..
```

### 2. Переменные окружения

```bash
cp .env.example .env           # red team
cp eval/.env.example eval/.env  # RAG eval
```

| Файл | Ключевые переменные |
|---|---|
| `.env` | `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` |
| `eval/.env` | `OPENROUTER_API_KEY`, `JUDGE_MODEL` |

### 3. Запустить дашборд

```bash
cd web && npm run dev
# → http://localhost:3000
```

---

## Модуль 1 — Security (Red Team)

Запускает атаки из `config/attack_config.yaml` против целевой модели и оценивает успешность через LLM-судью.

```bash
source .venv/bin/activate

# Запуск с настройками по умолчанию
python scripts/run_redteam.py

# Выбрать цель и судью
python scripts/run_redteam.py --target qwen-72b --judge qwen-72b-or
```

Результаты сохраняются в `results/*.parquet` и отображаются во вкладке **Security** дашборда.

**Вкладка Security показывает:**
- Security Score и ASR (Attack Success Rate)
- Breakdown по OWASP LLM Top 10 категориям
- Trend по истории сканов
- Таблица логов с фильтрами, экспорт PDF / MD / JSON

---

## Модуль 2 — RAG Quality Eval

Оценивает качество ответов RAG-бота по 4 метрикам через LLM-судью.

### Метрики

| Метрика | Порог | Что проверяет |
|---|---|---|
| **AR** Answer Relevancy | ≥ 0.7 | Ответ соответствует вопросу |
| **FA** Faithfulness | ≥ 0.8 | Нет галлюцинаций — ответ опирается на чанки |
| **CP** Contextual Precision | ≥ 0.7 | Нужные чанки идут первыми в выдаче |
| **CR** Contextual Recall | ≥ 0.6 | Все нужные чанки были найдены |

> FA, CP, CR требуют `retrieval_context` (список чанков из RAG). В офлайн-режиме считается только AR.

### Офлайн-прогон (датасет без живого API)

```bash
cd eval && source .venv/bin/activate

# Быстрая проверка — 1 вопрос
python scripts/run_eval.py --input datasets/dataset.json --limit 1

# Полный датасет
python scripts/run_eval.py --input datasets/20260329_173829_exp_top_k_10_dataset.json

# Другой судья / меньше параллелизма
python scripts/run_eval.py --input datasets/dataset.json --judge qwen-235b-or --workers 3
```

### Онлайн-прогон (все 4 метрики через живой API)

```bash
# 1 вопрос — проверить что API доступен
python scripts/run_eval.py \
  --input datasets/20260329_173829_exp_top_k_10_dataset.json \
  --online --api-url https://your-api.example.com --limit 1

# Полный датасет
python scripts/run_eval.py \
  --input datasets/20260329_173829_exp_top_k_10_dataset.json \
  --online --api-url https://your-api.example.com
```

### Pytest-тесты

Тест вызывает API **один раз на вопрос**, переиспользует ответ для всех метрик.

```bash
cd ..  # корень проекта

# Один вопрос
pytest tests/eval/ -v -k "TC-001" --api-url https://your-api.example.com

# Категория
pytest tests/eval/ -v -k "transfers" --api-url https://your-api.example.com

# Одна метрика по всем вопросам
pytest tests/eval/ -v -k "test_answer_relevancy" --api-url https://your-api.example.com
```

### Перегенерировать отчёт

```bash
cd eval
python eval_rag_metrics.py --report-only results/<папка_прогона>
```

### Результаты прогона

В `eval/results/<timestamp>_<имя_датасета>/`:

| Файл | Содержимое |
|---|---|
| `report.md` | Читаемый отчёт с саммари, таблицами и комментариями судьи |
| `metrics.json` | Детальные результаты (score, passed, reason) по каждой записи |
| `metrics.csv` | То же, табличный формат для Excel / Pandas |
| `api_responses.json` | Сырые ответы RAG-API (вопрос → ответ + чанки) |
| `errors_log.json` | Ошибки: API-таймауты, невалидный JSON судьи |

Результаты автоматически появляются во вкладке **Качество RAG** дашборда.

---

## Судьи (RAG eval)

Настраиваются в `eval/config/targets.yaml`:

| Имя | Модель | Рекомендация |
|---|---|---|
| `qwen-72b-or` | qwen/qwen-2.5-72b-instruct | **Дефолт** — быстро и качественно |
| `qwen-235b-or` | qwen/qwen3-235b-a22b | Максимальное качество |
| `gpt4o-mini-or` | openai/gpt-4o-mini | Быстрый альтернативный |
| `gpt4o-or` | openai/gpt-4o | Точный, дороже |
| `gemini-flash` | google/gemini-flash-1.5 | Самый дешёвый |
| `gigachat` | GigaChat-Pro | Российская модель |

---

## Датасет

Датасеты лежат в `eval/datasets/`. Формат:

```json
[
  {
    "id": "TC-001",
    "category": "kids_complex",
    "question": "Что такое Лес чудес?",
    "expected_output": "Эталонный ответ...",
    "actual_output": "Baseline-ответ..."
  }
]
```

Конвертировать из top_k формата:

```bash
python eval/scripts/convert_dataset.py eval/top_k/file.json
# → eval/datasets/file_dataset.json
# → eval/datasets/file_dataset.csv
```

---

## Типичные проблемы

**FA / CP / CR не считаются в офлайн-прогоне**  
В датасете нет поля `retrieval_context`. Используйте `--online` — чанки берутся из живого API.

**Ошибки 429 (Rate Limit)**
```bash
python scripts/run_eval.py --input file.json --workers 3
```

**504 Gateway Timeout**  
API нагружен. Уменьшите параллелизм (`--workers 1`) или повторите позже.

**Дашборд не открывается**
```bash
cd web && kill $(lsof -ti:3000) && npm run dev
```
