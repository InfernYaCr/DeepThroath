# DeepThroath — Предложения по улучшению

> Сгенерировано: 2026-03-30. Анализ на основе текущего состояния кодовой базы.

---

## 🔴 Критические (исправить в первую очередь)

| # | Проблема | Файл | Описание | Статус |
|---|----------|------|----------|--------|
| 1 | **API ключи без валидации** | `src/red_team/runner.py` | `os.environ["OPENROUTER_API_KEY"]` падает с криптичным `KeyError` вместо понятного сообщения пользователю | ✅ Исправлено — `_require_env()` с понятным сообщением |
| 2 | **Нет таймаута на вызовы моделей** | `src/red_team/runner.py` | Зависший запрос к API блокирует весь скан бесконечно — нет `timeout` параметра | ✅ Исправлено — `API_TIMEOUT = 60s` для Anthropic и OpenRouter |
| 3 | **Silent failure в storage** | `src/data/storage.py` | `except Exception: continue` — битые parquet-файлы исчезают без предупреждения в логах | ✅ Исправлено — `logging.warning` с именем файла и причиной |
| 4 | **Нет защиты в `load_history()`** | `src/data/storage.py` | Один битый файл истории ломает всю вкладку "Тренд" с необработанным исключением | ✅ Исправлено — try/except на каждый файл, пустые пропускаются |
| 5 | **Нет обработки ошибок в callbacks** | `src/red_team/runner.py` | Сетевые ошибки и таймауты API не перехватываются, крашат весь скан | ✅ Исправлено — try/except в обоих callbacks, ошибка как ответ модели |

---

## 🟠 Важные (следующий приоритет)

### Производительность
- ✅ `load_history()` читает ВСЕ parquet-файлы при каждом рефреше — добавлен `@st.cache_data(ttl=60)`
- ✅ Двойной вызов `get_owasp_category()` на каждую строку в `charts.py` — исправлено, вызов один раз на строку
- ✅ `st.dataframe()` в логах без пагинации — добавлена постраничная навигация (50 записей/страница)

### Конфигурация
- ✅ Версии зависимостей не зафиксированы — зафиксированы точные версии в `requirements.txt` (deepteam==1.0.6 и др.)
- ✅ Пресеты судей захардкожены в `judges.py` — добавлена `register_custom_presets()`, новые пресеты можно задавать прямо в YAML через `judge_custom_presets:`
- ✅ Нет валидации YAML-конфигов через Pydantic — добавлена валидация через Pydantic 2 в `run_redteam.py`
- ✅ URL OpenRouter захардкожен в `runner.py` — теперь берётся из `OPENROUTER_BASE_URL` env, fallback на дефолтный

### CLI
- ✅ При неправильном имени `--target` не показывает доступные варианты — теперь выводит список: `Available targets: default, strict, qwen-7b, ...`

---

## 🟡 UX / Dashboard

| Улучшение | Приоритет | Описание | Статус |
|-----------|-----------|----------|--------|
| **Сравнение двух сканов** | Высокий | Выбрать два скана и увидеть дельту по каждой категории OWASP: что улучшилось, что ухудшилось, где ASR изменился | ✅ Сделано — вкладка "Сравнение" |
| **Индикатор загрузки** при старте | Средний | Сейчас blank screen пока грузятся parquet — добавить `st.spinner("Загрузка результатов...")` | ✅ Сделано |
| **Пагинация логов** | Средний | При большом количестве записей `st.dataframe()` зависает в браузере | ✅ Сделано |
| **Экспорт диалогов JSON** | Средний | CSV обрезает колонку `conversations` — добавить кнопку "Скачать JSON" с полными диалогами (атака + ответ + вердикт судьи) | ✅ Сделано — кнопка рядом с CSV |

---

## 🔵 Тесты (покрытие ~85%)

**Протестировано:** 89 тестов, все проходят (`pytest tests/ -v`)

| Модуль | Тест-файл | Тесты | Что покрыто |
|--------|-----------|-------|-------------|
| `src/data/storage.py` | `test_storage.py` | ✅ 12 | save/load/history/list_scan_files, битые файлы, пустая история |
| `src/reports/generator.py` | `test_generator.py` | ✅ 11 | Security score edge cases, пустой DF, required keys |
| `src/red_team/severity.py` | `test_severity.py` | ✅ 11 | OWASP registry completeness, subtype matching, fallback |
| `scripts/run_redteam.py` | `test_cli.py` | ✅ 9 | CLI arg parsing, Pydantic validation, exit codes |
| `src/reports/pdf_export.py` | `test_pdf_export.py` | ✅ 17 | HTML+Markdown рендеринг, score delta, owasp_results, WeasyPrint mock |
| `src/dashboard/app.py` | `test_app_logic.py` | ✅ 14 | KPI-расчёты, cat_map, логика вкладки "Сравнение" |
| `src/red_team/runner.py` | `test_runner.py` | ✅ 3 | Callbacks, API calls |
| `src/data/transformer.py` | `test_transformer.py` | ✅ 5 | OWASP fields, ASR calc, empty handling |
| `src/dashboard/charts.py` | `test_charts.py` | ✅ 5 | Chart rendering |

> Streamlit-компоненты (`st.*`) не тестируются headlessly — бизнес-логика app.py вынесена в `test_app_logic.py`.

---

## 🚀 Новые фичи (Backlog)

| Фича | Ценность | Сложность |
|------|----------|-----------|
| Batch scanning — несколько targets за один запуск | Высокая | Средняя |
| Webhook / Slack alert при пробитии ASR порога | Средняя | Средняя |
| Scan comparison / diff view в дашборде | Высокая | Средняя |
| Экспорт диалогов в JSON (доказательная база) | Средняя | Низкая |
| Интеграция с LLMGuard / Presidio | Средняя | Высокая |
| Multi-language атаки (enabled: true для Multilingual) | Средняя | Низкая |
| Поддержка локальных моделей через Ollama | Средняя | Средняя |
| Интеграция с Jira/Linear — авто-тикеты на уязвимости | Низкая | Средняя |

---

## Рекомендуемый порядок реализации

1. **Таймаут на API-вызовы** + понятные сообщения об ошибке — 5 строк, критично
2. **`@st.cache_data` для `load_history()`** — 1 строка, заметный прирост скорости
3. **Тесты для `storage` и `generator`** — защита от регрессий
4. **Сравнение двух сканов** в дашборде — наибольшая ценность для пользователя
5. **Пакетное тестирование** нескольких targets
