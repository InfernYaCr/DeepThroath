# Changelog - DeepThroath Migration (Next.js)

Все изменения, внесенные в ходе миграции платформы DeepThroath с Streamlit на Next.js.

## [Phase 1] Core Migration (Security/Red Teaming)
- **Framework:** Полный переход на Next.js (App Router).
- **Data Engine:** Интеграция `@duckdb/node-api` для высокопроизводительной обработки файлов `.parquet` напрямую из файловой системы.
- **Backend API:** Создан `/api/data` для динамической загрузки данных сканирований и метаданных.
- **Dashboard UI:** Реализован многовкладочный интерфейс (Tabs) с разделами:
    - **Overview:** Общий Pie Chart по статусам прохождения.
    - **OWASP:** Столбчатая диаграмма ASR по категориям уязвимостей.
    - **Trend:** Линейный график истории защищенности.
    - **Comparison:** Продвинутый инструмент A/B сравнения двух сканов с расчетом дельты ASR (улучшение/ухудшение).
    - **Logs:** Таблица детальных логов атак.

## [Phase 2] Quality RAG (Eval) Dashboard
- **Backend API:** Реализован `/api/eval` для автоматического обнаружения и парсинга `metrics.json` из `eval/results/`.
- **Eval Dashboard:** Создана страница `/eval` для визуализации качества ответов (Answer Relevancy, Faithfulness).
- **Details View:** Использование `Accordion` для глубокого анализа каждого вопроса: фактический ответ, ожидаемый ответ, аргументация "судьи" (judge reasoning) и извлеченный контекст.

## [Phase 3] UI/UX & Premium Design (Neo-Glassmorphism)
- **Typography:** Переход на шрифтовую систему `Inter` (с поддержкой Cyrillic) для улучшения читаемости и устранения "скачков" размеров. Стандартизированы веса (Normal/Medium/Semibold).
- **Visuals:** Применена концепция **Neo-Glassmorphism**:
    - Добавлены Aurora Background эффекты (размытые светящиеся пятна в фоне).
    - Карточки и панели переведены на стеклянный стиль (`backdrop-blur-3xl`, `bg-white/5`, `border-white/10`).
    - Увеличены отступы (padding) и размеры шрифтов для соответствия Enterprise-стандартам.
- **Layout:** Унифицирована навигация в хедере для быстрого переключения между безопасностью (Red Teaming) и качеством (Eval).

## Bug Fixes & Refactoring
- **Build System:** Исправлены критические ошибки парсинга Turbopack, связанные с использованием неэкранированных бэктиков (\`) в TSX файлах.
- **Base UI Integration:** Исправлены пропсы `Accordion` для соответствия новым библиотекам Shadcn (Base UI вместо Radix).
- **Comparison Logic:** Доработан алгоритм вычисления дельты ASR для корректного отображения процентов изменений.
