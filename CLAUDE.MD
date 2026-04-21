# DeepThroath: AI Coding Assistant Guidelines

**Основано на методологии Андрея Карпатого для LLM-ассистентов**
**Проект:** DeepThroath — Red Team Security Testing & RAG Quality Evaluation Platform
**Версия:** 2.0 (обновлено 2026-04-21)

---

## О проекте

DeepThroath — платформа для автоматизированного тестирования безопасности LLM моделей (Red Teaming) и оценки качества RAG систем через DeepEval метрики.

**Стек:**
- Frontend: Next.js 16.2.2, React 19, TypeScript, Tailwind CSS
- Backend: Python 3.11, FastAPI (в разработке), Streamlit (deprecated)
- LLM: OpenAI, Anthropic, DeepSeek, Gemini
- Testing: DeepEval, pytest
- Data: DuckDB, Parquet, Pandas

**Статус:** Рефакторинг для деплоя (см. `ARCHITECTURE_REFACTORING.md`)

---

## Четыре принципа работы (по Карпатому)

### 1. Думай перед кодированием — не угадывай, спрашивай

**Директива:** Не делай предположений. Не скрывай путаницу. Покажи варианты.

**Правила:**
- Формулируй предположения явно, если что-то неясно
- Задавай вопросы при неоднозначности требований
- Предлагай альтернативы, если есть несколько подходов
- Останавливайся и называй проблему, если что-то запутано

**Пример:**
```
Плохо:
User: "Добавь экспорт для Red Team"
AI: [Создает CSV без уточнений]

Хорошо:
User: "Добавь экспорт для Red Team"
AI: "Уточни: формат (CSV/JSON/Parquet)? Какие поля? Текущая сессия или вся история?"
```

---

### 2. Простота прежде всего — минимум кода

**Директива:** Только необходимый код. Никакой спекуляции.

**Запреты:**
- Не добавляй незапрошенные фичи
- Не создавай абстракции для одноразового кода
- Не делай гибкость без запроса
- Не добавляй error handling для невозможных сценариев
- Не пиши 200 строк, если можно 50

**Пример:**
```python
# Плохо (overengineering)
class LLMProviderFactory:
    def __init__(self):
        self._providers = {}
        self._strategies = {}
        # 100+ строк для одного вызова

# Хорошо (KISS)
def call_model(provider: str, prompt: str) -> str:
    if provider.startswith("openai"):
        return openai.chat.completions.create(...)
    elif provider.startswith("anthropic"):
        return anthropic.messages.create(...)
```

**Тест на overengineering:** Назовет ли senior инженер это overcomplicated? Если да — упрости.

---

### 3. Хирургическая точность — трогай только необходимое

**Директива:** Редактируй только то, что нужно. Не улучшай соседний код.

**Правила:**
- Изменяй только строки, связанные с задачей
- Не рефактори работающий код рядом
- Не форматируй соседние комментарии
- Не удаляй мертвый код без запроса
- Следуй существующему стилю проекта

**Критерий:** Каждая измененная строка должна напрямую относиться к запросу пользователя.

---

### 4. Ориентация на цель — определи критерии успеха

**Директива:** Сформулируй критерий успеха. Итерируйся до проверки.

**Трансформация задач:**
- Расплывчато: "Добавь валидацию" → Проверяемо: "Напиши тесты, затем реализуй чтобы они прошли"
- Расплывчато: "Исправь баг" → Проверяемо: "Воспроизведи в тесте, затем исправь"
- Расплывчато: "Рефактори код" → Проверяемо: "Убедись что тесты проходят до и после"

**Правило:** LLM отлично итерируются к цели. Не говори ЧТО делать — говори КАКОЙ результат нужен.

---

## Технические стандарты

### TypeScript
- `strict: true` (уже включен)
- Избегать `any` — использовать `unknown` в catch
- Использовать Zod для runtime валидации (TODO)
- Не использовать `@ts-ignore` без комментария

### Python
- Type hints для всех функций (TODO: mypy в CI)
- Pydantic модели для API схем
- Docstrings для публичных функций (Google style)
- PEP 604: `str | None` вместо `Optional[str]`

**Пример:**
```python
def run_redteam(
    target: str,
    num_attacks: int = 10,
    api_key: str | None = None
) -> Path:
    """
    Запуск Red Team сканирования.

    Args:
        target: Провайдер модели (openai:gpt-4o, anthropic:claude-sonnet-4)
        num_attacks: Количество атак (1-1000)
        api_key: API ключ провайдера (если не в env)

    Returns:
        Path к файлу с результатами (results/latest.parquet)

    Raises:
        ValueError: Если target невалиден или num_attacks вне диапазона
    """
```

### Тестирование
- Один тест проверяет одно поведение
- Arrange-Act-Assert структура
- Моки для внешних API
- Фикстуры в `conftest.py`

### Git Commits
```
<type>(<scope>): <краткое описание>

<детали>
```

**Типы:** feat, fix, refactor, test, docs, chore

---

## Критичные проблемы (блокеры деплоя)

1. **child_process.spawn в Next.js API routes**
   - Файлы: `web/src/app/api/run/route.ts`, `web/src/app/api/runner/route.ts`
   - Проблема: Таймаут на serverless (Vercel/Netlify)
   - Решение: Миграция на FastAPI (см. `ARCHITECTURE_REFACTORING.md`)
   - Приоритет: P0 — НЕМЕДЛЕННО

2. **Отсутствие FastAPI backend**
   - Статус: В разработке (Фаза 1)
   - Файлы: `src/api/main.py` (создать), `src/api/schemas.py` (создать)
   - Приоритет: P0 — НЕМЕДЛЕННО

3. **Временные конфиг-файлы остаются при крашах**
   - Паттерн: `.tmp_api_config_*.json`
   - Решение: Передавать через HTTP body к FastAPI
   - Приоритет: P1 — ВАЖНО

4. **Дублирование Streamlit дашбордов**
   - Директория: `src/dashboard/` (9 файлов, 2689 строк)
   - Статус: Deprecated, удалить
   - Приоритет: P1 — ВАЖНО

---

## Ключевые файлы проекта

- `ARCHITECTURE_REFACTORING.md` — План рефакторинга, текущая архитектура
- `README.md` — Инструкции для пользователей
- `requirements.txt` — Python зависимости
- `web/package.json` — Next.js зависимости

**Структура:**
```
DeepThroath/
├── src/api/              # CREATE: FastAPI микросервис
├── src/red_team/         # Логика Red Team атак
├── src/dashboard/        # DELETE: Streamlit (deprecated)
├── eval/                 # RAG Evaluation (DeepEval)
├── web/src/app/          # Next.js UI
└── scripts/              # CLI утилиты
```

---

## Инструкции для AI-ассистента

### Перед любой задачей:
1. Прочитай `ARCHITECTURE_REFACTORING.md` если задача связана с архитектурой
2. Проверь текущую ветку: `feat/provider-comparison` или `main`
3. Найди связанные файлы через Glob/Grep
4. Спроси о неясностях — не угадывай требования

### При написании кода:
1. Следуй 4 принципам Карпатого
2. Используй существующие паттерны из кодовой базы
3. Пиши тесты для новой функциональности
4. Обновляй документацию если меняешь API

### При рефакторинге:
1. Хирургическая точность — только необходимые изменения
2. Проверяй тесты до и после
3. Не удаляй мертвый код без запроса
4. Сохраняй обратную совместимость

### При отладке:
1. Воспроизведи проблему в тесте
2. Найди root cause — не маскируй симптомы
3. Исправь минимально — не рефактори всё
4. Убедись что тест проходит после фикса

---

## Чек-лист code review

- [ ] Все изменения напрямую связаны с задачей (принцип 3)
- [ ] Код максимально прост — нет overengineering (принцип 2)
- [ ] Все предположения явно озвучены (принцип 1)
- [ ] Есть критерий успеха — тесты проходят (принцип 4)
- [ ] TypeScript: нет `any`, все типы строгие
- [ ] Python: есть type hints, docstrings, Pydantic схемы
- [ ] Тесты добавлены для новой функциональности
- [ ] Существующие тесты не сломаны
- [ ] Нет временных файлов в коммите
- [ ] Commit message следует формату

---

**Методология:** Основано на рекомендациях [Андрея Карпатого](https://github.com/forrestchang/andrej-karpathy-skills)

---

## Источники

- [Karpathy's CLAUDE.md Skills File: The Complete Guide](https://antigravity.codes/blog/karpathy-claude-code-skills-guide)
- [Andrej Karpathy-Inspired Guidelines for Claude Code](https://aitoolly.com/ai-news/article/2026-04-16-andrej-karpathy-inspired-guidelines-for-claude-code-optimizing-llm-performance-via-claudemd)
- [Andrej Karpathy's Claude Code Skills | Medium](https://medium.com/data-science-in-your-pocket/andrej-karpathys-claude-code-skills-3db42cc634c8)
