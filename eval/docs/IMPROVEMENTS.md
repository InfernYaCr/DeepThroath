# DeepPulse — Improvements Log

## Реализованные улучшения

### v1.0 — Интеграция с DeepThroath (2026-04-02)

**YAML-конфигурация судей**
- Добавлены `eval/config/targets.yaml` и `eval/config/eval_config.yaml`
- Формат аналогичен `config/targets.yaml` DeepThroath — единая концепция конфигурации
- CLI `run_eval.py --judge <name>` вместо переменных окружения

**Programmatic API**
- Добавлена функция `run_eval()` в `eval_rag_metrics.py`
- Позволяет вызывать eval pipeline из unified_app.py без subprocess

**Data Layer**
- Создан `src/data/eval_storage.py`
- `list_eval_runs()`, `load_eval_run()`, `load_latest_eval()`, `quality_score()`
- Автоопределение папок прогонов в `eval/results/`

**Визуализация**
- Создан `src/dashboard/quality_charts.py` — 4 Plotly-графика
- `ar_by_category_bar()` — средний AR по категориям
- `ar_distribution_histogram()` — распределение scores
- `quality_trend_line()` — тренд Quality Score во времени
- `faithfulness_vs_relevancy_scatter()` — корреляция двух метрик

**Unified Dashboard**
- Создан `src/dashboard/unified_app.py`
- Sidebar: Сводка / Безопасность / Качество RAG
- Сводная страница: 4 KPI (Security Score + Quality Score + Security ASR + Quality Pass Rate)
- Раздел "Качество RAG": 4 вкладки с графиками и деталями

**Тесты**
- `tests/test_eval_storage.py` — 10 тестов
- `tests/test_quality_charts.py` — 13 тестов
- Полная изоляция через monkeypatch

---

## Запланированные улучшения

> Подробнее — в [ROADMAP.md](ROADMAP.md)

| # | Улучшение | Приоритет |
|---|-----------|-----------|
| 1 | GitHub Actions CI/CD | 🔴 Высокий |
| 2 | Contextual Precision + Recall metrics | 🔴 Высокий |
| 3 | PDF-отчёт | 🟡 Средний |
| 4 | Демо-данные | 🟡 Средний |
| 5 | Side-by-side сравнение прогонов | 🟡 Средний |
| 6 | Ollama judge | 🟢 Низкий |
| 7 | Slack / Telegram алерты | 🟢 Низкий |
| 8 | Batch-режим (несколько конфигов) | 🟢 Низкий |
| 9 | JUnit XML для CI/CD | 🟢 Низкий |
| 10 | REST API | 🟢 Низкий |
