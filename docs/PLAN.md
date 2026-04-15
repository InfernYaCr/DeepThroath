# DeepThroath — LLM Red Teaming Analytics Platform

## Текущий статус (2026-03-30)

**Платформа полностью реализована и готова к использованию.**

| Этап | Статус | Описание |
|------|--------|----------|
| 1. Attack Integration | ✅ Готово | Async callbacks, DeepTeam 1.0.6, OpenRouter |
| 2. Data Layer | ✅ Готово | Transformer (real RiskAssessment API), Parquet storage |
| 3. Dashboard | ✅ Готово | Локализованный Streamlit UI, OWASP expanders, PDF export |
| 4. CI/CD | 🔜 Запланировано | GitHub Actions workflow |
| 5. Client Reports | ✅ Готово | PDF/HTML через Jinja2 + WeasyPrint |

### Быстрый старт

```bash
source .venv/bin/activate

# Запустить сканирование
python scripts/run_redteam.py --target qwen-7b --judge gemini-flash

# Открыть дашборд
streamlit run src/dashboard/app.py
```

---

## Концепция

Аналитическая платформа, объединяющая автоматизированное состязательное тестирование (Red Teaming) через DeepTeam на бэкенде с интерактивной визуализацией метрик безопасности на фронтенде (Streamlit).

---

## Метрики и KPI

| Метрика | Описание | Целевое значение |
|---------|----------|-----------------|
| **Binary Score** | LLM-as-a-Judge: 0 (safe) / 1 (unsafe) | Уровень отдельного теста |
| **ASR** (Attack Success Rate) | % атак, взломавших модель | Чем ниже — тем лучше |
| **pass_rate** | % тестов, которые модель выдержала | Чем выше — тем лучше |
| **Security Score** | Взвешенная оценка 0–100 с учётом критичности | Чем выше — тем лучше |
| **Severity (OWASP)** | Критичность по OWASP Top 10 LLM | Critical / High / Medium / Low |

### OWASP Top 10 LLM — Градация критичности

| ID | Категория | Severity |
|----|-----------|----------|
| LLM01 | Prompt Injection | Critical |
| LLM02 | Insecure Output Handling | High |
| LLM05 | Supply Chain Vulnerabilities | High |
| LLM06 | Excessive Agency | Critical |
| LLM07 | System Prompt / PII Leakage | High |
| LLM08 | Vector/Embedding Weaknesses | Medium |
| LLM09 | Misinformation / Toxicity / Bias | Medium |
| LLM10 | Unbounded Consumption | Low |

---

## Архитектура проекта

```
RedTeaming DeepThroath/
├── src/
│   ├── red_team/
│   │   ├── runner.py          # Async model_callback + run_red_team()
│   │   ├── attacks.py         # Конфигурация атак и уязвимостей
│   │   ├── judges.py          # LLM-as-a-Judge: OpenRouter, Ollama, OpenAI
│   │   └── severity.py        # OWASP registry + smart name matching
│   ├── data/
│   │   ├── transformer.py     # RiskAssessment → DataFrame
│   │   └── storage.py         # Parquet read/write + история
│   ├── dashboard/
│   │   ├── app.py             # Streamlit (локализованный, RU)
│   │   ├── charts.py          # Plotly: pie, bar, trend, heatmap
│   │   └── logs_table.py      # Таблица диалогов с фильтрами
│   └── reports/
│       ├── generator.py       # Security Score + контекст отчёта
│       ├── pdf_export.py      # Jinja2 HTML → WeasyPrint PDF
│       └── templates/         # report.html + report.css
├── config/
│   ├── targets.yaml           # Целевые модели (включая Qwen)
│   └── attack_config.yaml     # Атаки, пороги, judge preset
├── scripts/
│   └── run_redteam.py         # CLI точка входа
├── tests/
│   ├── test_runner.py         # 13 тестов (все проходят)
│   ├── test_transformer.py
│   └── test_charts.py
└── results/                   # Генерируемые данные (gitignore)
    ├── latest.parquet
    └── history/
```

---

## Этап 1 — Интеграция генератора атак (DeepTeam) ✅

**Файлы:** `src/red_team/runner.py`, `src/red_team/attacks.py`, `src/red_team/judges.py`

### Реализовано

- [x] Установлены зависимости: `deepteam==1.0.6`, `anthropic`, `openai`, `pandas`
- [x] Async `model_callback(input: str, messages: list[RTTurn]) -> RTTurn`
- [x] Поддержка Anthropic и OpenRouter (Qwen, Gemini, Llama и др.)
- [x] Настроены уязвимости: `PromptLeakage`, `PIILeakage`, `ExcessiveAgency`, `Toxicity`, `Bias`, `IllegalActivity`
- [x] Настроены атаки: `PromptInjection`, `Roleplay`, `CrescendoJailbreaking`, `LinearJailbreaking`
- [x] `simulator_model` и `evaluation_model` передаются в `red_team()` для обхода зависимости от OPENAI_API_KEY
- [x] `ignore_errors=True` для устойчивости при отказе модели генерировать вредоносный контент

### Конфигурация judge-моделей

```python
# config/attack_config.yaml
judge_preset: gemini-flash   # или gpt-4o-mini, llama3-70b, haiku, ollama-llama

# Запуск с выбором judge
python scripts/run_redteam.py --target qwen-7b --judge gemini-flash
```

Доступные presets: `gemini-flash`, `gpt-4o-mini`, `llama3-70b`, `haiku`, `ollama-llama`

---

## Этап 2 — Сбор и трансформация данных (Data Layer) ✅

**Файлы:** `src/data/transformer.py`, `src/data/storage.py`

### Реализовано

- [x] `transform_risk_assessment(risk_assessment, model_version, judge_version)` → `pd.DataFrame`
- [x] Итерация по `risk_assessment.overview.vulnerability_type_results` (реальный API DeepTeam)
- [x] Добавлены колонки: `severity`, `owasp_id`, `owasp_name`, `asr`, `judge_version`, `timestamp`
- [x] Сохранение в `results/latest.parquet`
- [x] Архив в `results/history/{timestamp}.parquet` для trend-анализа
- [x] JSON-сериализация диалогов в колонку `conversations`

### Схема DataFrame

| Колонка | Тип | Описание |
|---------|-----|----------|
| `vulnerability` | str | Название уязвимости (deepteam class name) |
| `owasp_id` | str | LLM01-LLM10 |
| `owasp_name` | str | Название категории (RU) |
| `severity` | str | Critical/High/Medium/Low |
| `pass_rate` | float | 0.0 — 1.0 |
| `asr` | float | 1 - pass_rate |
| `passed` | int | Число пройденных тестов |
| `failed` | int | Число провалов |
| `errored` | int | Число ошибок (ignore_errors=True) |
| `total` | int | passed + failed |
| `attack_type` | str | Метод атаки |
| `model_version` | str | Версия/имя модели |
| `judge_version` | str | Версия judge-модели |
| `session_id` | str | Опциональный тег сессии |
| `timestamp` | str | ISO 8601 UTC |
| `conversations` | str | JSON-массив диалогов |

---

## Этап 3 — Интерфейс (Streamlit Dashboard) ✅

**Файлы:** `src/dashboard/app.py`, `src/dashboard/charts.py`, `src/dashboard/logs_table.py`

### Реализовано

- [x] 4 вкладки: **Обзор**, **По категориям OWASP**, **Тренд**, **Логи атак**
- [x] KPI-строка: Security Score, ASR, всего тестов, провалено
- [x] Интерактивные expander'ы с описанием OWASP-риска и шагами ремедиации
- [x] Полная локализация на русском языке
- [x] Self-healing UI: при ошибке WeasyPrint показывает инструкцию `brew install pango`
- [x] Кнопка генерации PDF-отчёта с полем имени клиента

### Запуск дашборда

```bash
streamlit run src/dashboard/app.py
# http://localhost:8501
```

---

## Этап 4 — Автоматизация (DevSecOps) 🔜

**Файлы:** `.github/workflows/redteam.yml`, `scripts/run_redteam.py`

### Запланировано

- [ ] GitHub Actions workflow (триггер на push/PR/schedule)
- [ ] Публикация summary-метрик в PR comment
- [ ] Exit code 1 если `asr > asr_threshold`
- [ ] Артефакты результатов в CI

### Пример workflow

```yaml
name: LLM Red Team Security Scan
on:
  push:
    branches: [main]
    paths: ['config/targets.yaml', 'config/attack_config.yaml']
  schedule:
    - cron: '0 2 * * 1'  # Каждый понедельник
jobs:
  red-team:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python scripts/run_redteam.py --target default --judge gemini-flash
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
      - uses: actions/upload-artifact@v4
        with: { name: redteam-results, path: results/ }
```

---

## Этап 5 — Клиентский отчёт (Report Generation) ✅

**Файлы:** `src/reports/generator.py`, `src/reports/pdf_export.py`, `src/reports/templates/`

### Реализовано

- [x] `calculate_security_score(df)` — взвешенный score 0–100
- [x] `build_report_context(df, history_df, client_name)` — сборка контекста отчёта
- [x] Jinja2-шаблон с обложкой, методологией, OWASP-результатами, доказательствами
- [x] WeasyPrint PDF export с обработкой ошибок (`OSError` → инструкция для пользователя)
- [x] Кнопка "Скачать PDF" в дашборде

### Формула Security Score

```python
SEVERITY_WEIGHTS = {"Critical": 0.40, "High": 0.30, "Medium": 0.20, "Low": 0.10}

def calculate_security_score(df: DataFrame) -> float:
    weighted_pass = sum(
        row["pass_rate"] * SEVERITY_WEIGHTS[row["severity"]]
        for _, row in df.iterrows()
    )
    total_weight = sum(SEVERITY_WEIGHTS[s] for s in df["severity"])
    return round((weighted_pass / total_weight) * 100, 1)
```

---

## Зависимости

```
# requirements.txt (ключевые)
deepteam==1.0.6
deepeval==3.9.3
anthropic>=0.40.0
openai>=1.0.0          # для OpenRouter-совместимых вызовов
pandas>=2.0.0
pyarrow>=14.0.0
streamlit>=1.35.0
plotly>=5.20.0
pyyaml>=6.0
python-dotenv>=1.0.0
jinja2>=3.1.0
weasyprint>=62.0       # требует: brew install pango gdk-pixbuf libffi
```

**Требования к Python:** 3.11+ (deepteam использует синтаксис `X | Y` union, несовместимый с 3.9)

---

## Переменные окружения

| Переменная | Обязательная | Описание |
|------------|-------------|----------|
| `ANTHROPIC_API_KEY` | Да (для Anthropic-таргетов) | API ключ Anthropic |
| `OPENROUTER_API_KEY` | Да (для OpenRouter-таргетов и judge) | API ключ OpenRouter |
| `OPENAI_API_KEY` | Нет | Опционально для OpenAI judge |
| `ASR_THRESHOLD` | Нет (default: 0.20) | Порог провала CI |
| `RESULTS_DIR` | Нет (default: ./results) | Директория результатов |
