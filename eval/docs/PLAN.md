# DeepPulse — Implementation Plan

## Текущий статус (2026-04-02)

**Pipeline полностью реализован и интегрирован с DeepThroath.**

| Этап | Статус | Описание |
|------|--------|----------|
| 1. Eval Pipeline | ✅ Готово | ThreadPoolExecutor, DeepEval metrics, checkpoint |
| 2. YAML Config | ✅ Готово | targets.yaml + eval_config.yaml (как в DeepThroath) |
| 3. Data Layer | ✅ Готово | eval_storage.py, quality_score(), list_eval_runs() |
| 4. Charts | ✅ Готово | 4 Plotly графика: bar, histogram, trend, scatter |
| 5. Unified Dashboard | ✅ Готово | unified_app.py: безопасность + качество в одном UI |
| 6. Tests | ✅ Готово | 23 теста: eval_storage (10) + quality_charts (13) |
| 7. CI/CD | 🔜 Запланировано | GitHub Actions workflow |

### Быстрый старт

```bash
# Из корня проекта DeepThroath
source .venv/bin/activate

# Запустить оценку качества
python eval/scripts/run_eval.py --input data/questions.json --judge gpt4o-mini-or

# Открыть unified dashboard
streamlit run src/dashboard/unified_app.py
# http://localhost:8501 → раздел "✅ Качество RAG"
```

---

## Этап 1 — Eval Pipeline ✅

**Файл:** `eval/eval_rag_metrics.py`

### Реализовано

- [x] `evaluate_record()` — thread worker, создаёт собственные экземпляры судьи и метрик
- [x] `AnswerRelevancyMetric` — Answer Relevancy через DeepEval
- [x] `FaithfulnessMetric` — Faithfulness через DeepEval (при наличии `retrieval_context`)
- [x] `OpenRouterJudge` — любая модель через OpenRouter API
- [x] `GigaChatJudge` — GigaChat с созданием клиента per call (thread-safety)
- [x] Checkpoint system — сохранение после каждой записи, восстановление при падении
- [x] `run_eval()` — programmatic API для интеграции с unified_app.py
- [x] `format_reason()` — постобработка "The score is X because" → "Оценка X:"
- [x] Системный промпт для судьи — reason на русском языке

### Параллелизм

```
MAX_WORKERS = 10 потоков
Каждый поток: собственный build_judge() + AnswerRelevancyMetric + FaithfulnessMetric
checkpoint_lock = threading.Lock() — защита записи в checkpoint.json
```

---

## Этап 2 — YAML Configuration ✅

**Файлы:** `eval/config/targets.yaml`, `eval/config/eval_config.yaml`

### Реализовано

- [x] `targets.yaml` — именованные профили судей (name/provider/model/threshold)
- [x] `eval_config.yaml` — параметры запуска (max_workers, default_judge, metrics)
- [x] Совместимый формат с `config/targets.yaml` DeepThroath
- [x] `run_eval.py` — CLI с `--judge <name>` (имя из targets.yaml)

### Доступные судьи

| Name | Provider | Model | Price |
|------|----------|-------|-------|
| `gpt4o-mini-or` | openrouter | openai/gpt-4o-mini | ~$0.15/1M |
| `gigachat` | gigachat | GigaChat-Pro | по тарифу |

---

## Этап 3 — Data Layer ✅

**Файл:** `src/data/eval_storage.py`

### Реализовано

- [x] `list_eval_runs()` — обнаружение всех прогонов в `eval/results/`
- [x] `load_eval_run(path)` — загрузка metrics.json → pd.DataFrame
- [x] `load_latest_eval()` — загрузка последнего прогона
- [x] `quality_score(df)` — среднее answer_relevancy_score × 100

---

## Этап 4 — Charts ✅

**Файл:** `src/dashboard/quality_charts.py`

### Реализовано

- [x] `ar_by_category_bar()` — средний AR по категориям (bar chart)
- [x] `ar_distribution_histogram()` — распределение AR scores (histogram)
- [x] `quality_trend_line()` — Quality Score и pass rate во времени (line chart)
- [x] `faithfulness_vs_relevancy_scatter()` — Faithfulness vs AR (scatter)

---

## Этап 5 — Unified Dashboard ✅

**Файл:** `src/dashboard/unified_app.py`

### Реализовано

- [x] Sidebar navigation: 📊 Сводка / 🔐 Безопасность / ✅ Качество RAG
- [x] Сводка: 4-column KPI (Security Score + Quality Score + Security ASR + Quality Pass Rate)
- [x] Безопасность: полный раздел из app.py (5 вкладок)
- [x] Качество RAG: 4 вкладки (Обзор / По категориям / Детали записей / Тренд)
- [x] Экспорт: скачать Markdown-отчёт из eval/results/

---

## Этап 6 — Tests ✅

**Файлы:** `tests/test_eval_storage.py`, `tests/test_quality_charts.py`

- [x] 10 тестов — eval_storage (все edge cases: пустые данные, отсутствующие колонки)
- [x] 13 тестов — quality_charts (все 4 графика + edge cases)
- [x] Изоляция через monkeypatch (EVAL_RESULTS_DIR → tmp_path)

---

## Этап 7 — CI/CD 🔜

**Файл:** `.github/workflows/eval.yml`

### Запланировано

- [ ] GitHub Actions workflow (триггер на push/PR/schedule)
- [ ] Публикация Quality Score в PR comment
- [ ] Exit code 1 если `quality_score < threshold`
- [ ] Артефакты: metrics.json + report.md

### Пример workflow

```yaml
name: DeepPulse Quality Evaluation
on:
  push:
    branches: [main]
    paths: ['eval/config/**', 'data/**']
  schedule:
    - cron: '0 3 * * 1'  # Каждый понедельник
jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r eval/requirements.txt
      - run: python eval/scripts/run_eval.py --input data/questions.json --judge gpt4o-mini-or
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
      - uses: actions/upload-artifact@v4
        with: { name: eval-results, path: eval/results/ }
```

---

## Зависимости

```
# eval/requirements.txt
deepeval
python-dotenv
openai
gigachat
```

**Основные зависимости (из requirements.txt проекта):**
- `pandas` — DataFrame для хранения результатов
- `plotly` — графики в unified dashboard
- `streamlit` — UI

**Требования к Python:** 3.10+ (deepeval использует синтаксис `X | Y` для типов)
