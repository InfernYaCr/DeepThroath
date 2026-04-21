# eval — RAG Quality Pipeline

Оценка качества RAG-ответов по четырём метрикам через LLM-судью.

## Метрики

| Метрика | Порог | Что измеряет |
|---|---|---|
| **AR** Answer Relevancy | 0.7 | Ответ соответствует вопросу |
| **FA** Faithfulness | 0.8 | Ответ основан на чанках, без галлюцинаций |
| **CP** Contextual Precision | 0.7 | Нужные чанки идут первыми в выдаче |
| **CR** Contextual Recall | 0.6 | Все нужные чанки были найдены |

> FA, CP, CR вычисляются только при наличии `retrieval_context`.
> В офлайн-режиме (датасет без чанков) считается только AR.

---

## Быстрый старт

```bash
cd eval
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Заполнить OPENROUTER_API_KEY в .env
```

---

## Структура

```
eval/
├── eval_rag_metrics.py     Основной pipeline
├── scripts/
│   ├── run_eval.py         CLI-запуск прогона
│   └── convert_dataset.py  Конвертер top_k → dataset
├── datasets/               Датасеты (JSON + CSV)
├── top_k/                  Исходные данные экспериментов top_k
├── results/                Результаты прогонов (генерируется авто)
├── config/
│   ├── eval_config.yaml    Настройки (max_workers, default_judge)
│   └── targets.yaml        Доступные LLM-судьи
└── .env.example            Шаблон переменных окружения
```

---

## Режимы запуска

| | Онлайн | Офлайн |
|---|---|---|
| Источник ответов | Живой API | Датасет |
| Метрики | AR + FA + CP + CR | Только AR (нет чанков) |
| Флаг | `--online --api-url URL` | _(по умолчанию)_ |

---

## Офлайн-режим

```bash
# 1 вопрос (быстрая проверка)
python scripts/run_eval.py --input datasets/dataset.json --limit 1

# Полный датасет
python scripts/run_eval.py --input datasets/20260329_173829_exp_top_k_10_dataset.json

# Другой судья
python scripts/run_eval.py --input datasets/dataset.json --judge qwen-235b-or

# Уменьшить параллелизм при 429 ошибках
python scripts/run_eval.py --input datasets/dataset.json --workers 3
```

---

## Онлайн-режим (все 4 метрики)

Вызывает `POST /api/v1/eval/rag`, получает свежие ответы и чанки из живого бота.

```bash
# Проверка — 1 вопрос
python scripts/run_eval.py \
  --input datasets/20260329_173829_exp_top_k_10_dataset.json \
  --online --api-url https://your-api.example.com --limit 1

# Первые 10 вопросов
python scripts/run_eval.py \
  --input datasets/20260329_173829_exp_top_k_10_dataset.json \
  --online --api-url https://your-api.example.com --limit 10

# Полный прогон, 3 потока
python scripts/run_eval.py \
  --input datasets/20260329_173829_exp_top_k_10_dataset.json \
  --online --api-url https://your-api.example.com --workers 3
```

---

## Pytest-тесты

Используют тот же датасет. API вызывается **один раз на вопрос** — ответ переиспользуется для всех метрик.

```bash
cd ..  # корень проекта

# Один вопрос
pytest tests/eval/ -v -k "TC-001" --api-url https://your-api.example.com

# Несколько вопросов
pytest tests/eval/ -v -k "TC-001 or TC-002 or TC-003" --api-url https://your-api.example.com

# Одна категория
pytest tests/eval/ -v -k "kids_complex" --api-url https://your-api.example.com

# Одна метрика по всем вопросам
pytest tests/eval/ -v -k "test_answer_relevancy" --api-url https://your-api.example.com

# Весь датасет
pytest tests/eval/ -v --api-url https://your-api.example.com
```

Сырые ответы API сохраняются в `tests/logs/<timestamp>_api_responses.json`.

> **Отличие от run_eval.py:** pytest — санити-чек (pass/fail).
> `run_eval.py` генерирует полный MD-отчёт и CSV, которые видны в дашборде.

---

## Файлы прогона

После `run_eval.py` в `results/<timestamp>_<имя_датасета>/`:

| Файл | Содержимое |
|---|---|
| `report.md` | Читаемый отчёт: саммари, таблицы, комментарии судьи |
| `metrics.json` | Детальные результаты (score, passed, reason) по каждой записи |
| `metrics.csv` | То же, табличный формат для Excel / Pandas |
| `api_responses.json` | Сырые ответы RAG-API: вопрос → ответ + список чанков |
| `errors_log.json` | Ошибки: API-таймауты, невалидный JSON от судьи |

Перегенерировать отчёт без повторного прогона:
```bash
python eval_rag_metrics.py --report-only results/<папка_прогона>
```

---

## Конвертер датасета

Преобразует top_k файл в формат с `id` и `category`:

```bash
python scripts/convert_dataset.py top_k/20260329_173829_exp_top_k_10.json
# → datasets/20260329_173829_exp_top_k_10_dataset.json
# → datasets/20260329_173829_exp_top_k_10_dataset.csv
```

| Из top_k | В датасет |
|---|---|
| `intent` | `category` |
| `user_query` | `question` |
| `expected_answer` | `expected_output` |
| `actual_answer` | `actual_output` |

---

## Судьи

Настраиваются в `config/targets.yaml`:

| Имя | Модель | Примечание |
|---|---|---|
| `qwen-72b-or` | qwen/qwen-2.5-72b-instruct | **Дефолт** |
| `qwen-235b-or` | qwen/qwen3-235b-a22b | Максимальное качество |
| `gpt4o-mini-or` | openai/gpt-4o-mini | Быстрый |
| `gpt4o-or` | openai/gpt-4o | Точный |
| `gemini-flash` | google/gemini-flash-1.5 | Дешёвый |
| `gigachat` | GigaChat-Pro | Российская модель |

Изменить дефолтного судью:
```yaml
# config/eval_config.yaml
default_judge: qwen-72b-or
max_workers: 3
```

---

## Переменные окружения

```bash
# eval/.env
JUDGE_PROVIDER=openrouter
JUDGE_MODEL=qwen/qwen-2.5-72b-instruct
OPENROUTER_API_KEY=sk-or-...

# Опционально
OPENAI_API_KEY=sk-...
GIGACHAT_CREDENTIALS=...
```

---

## Восстановление после сбоя

После каждой записи сохраняется `checkpoint.json`. При повторном запуске уже обработанные записи пропускаются:

```bash
# Прогон упал на 30/56 — повторный запуск продолжит с 31
python scripts/run_eval.py --input datasets/file.json --online
```

---

## Устранение проблем

**FA / CP / CR не считаются**
Используйте `--online` — без живого API чанки недоступны.

**Ошибки 429 (Rate Limit)**
```bash
python scripts/run_eval.py --input file.json --workers 2
```

**504 Gateway Timeout**
Уменьшите параллелизм или повторите позже. Завершённые записи сохранены в чекпоинте.

**Перегенерировать отчёт**
```bash
python eval_rag_metrics.py --report-only results/20260414_121501_<stem>
```
