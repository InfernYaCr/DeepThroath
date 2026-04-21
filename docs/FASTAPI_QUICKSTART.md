# FastAPI Migration — Quick Start

## Установка зависимостей

```bash
pip install -r requirements.txt
```

## Запуск FastAPI сервера

**Терминал 1: FastAPI**
```bash
uvicorn src.api.main:app --reload --port 8000
```

Swagger UI доступен по адресу: http://localhost:8000/docs

**Терминал 2: Next.js**
```bash
cd web/
npm run dev
```

UI доступен по адресу: http://localhost:3000

## Эндпоинты FastAPI

### Red Team
- `POST /api/runner/redteam` — запустить Red Team сканирование
  ```json
  {
    "target": "openai:gpt-4o",
    "num_attacks": 10,
    "system_prompt": null
  }
  ```

### RAG Evaluation
- `POST /api/runner/eval` — запустить RAG Evaluation
  ```json
  {
    "dataset": "mglk_rag_deepeval",
    "model": "gpt4o-mini-or",
    "metrics": ["answer_relevancy", "faithfulness"],
    "n_samples": 50
  }
  ```

### Job Status
- `GET /api/jobs/{job_id}/status` — получить статус задачи
- `GET /api/jobs` — список всех задач

### Health Check
- `GET /health` — проверка здоровья сервиса

## Переменные окружения

Создать `.env` файл:
```bash
# API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# FastAPI URL (для Next.js)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Тестирование

```bash
# Запустить FastAPI
uvicorn src.api.main:app --reload --port 8000

# В другом терминале
curl -X POST http://localhost:8000/api/runner/redteam \
  -H "Content-Type: application/json" \
  -d '{"target": "default", "num_attacks": 1}'

# Получить статус
curl http://localhost:8000/api/jobs/{job_id}/status
```

## Изменения

### Удалено
- ❌ `child_process.spawn` из Next.js API routes
- ❌ Временные конфиг-файлы (`.tmp_api_config_*.json`)
- ❌ Streamlit дашборды (`src/dashboard/`)
- ❌ Дубликаты: `web/src/app/api/run/route.ts`, `web/src/app/api/runner/redteam/route.ts`

### Добавлено
- ✅ FastAPI микросервис (`src/api/`)
- ✅ Pydantic валидация запросов
- ✅ Background tasks для долгих LLM операций
- ✅ In-memory job tracking (JSON)
- ✅ Polling endpoint для статуса задач

### Модифицировано
- 🔄 `scripts/run_redteam.py` — добавлена callable функция `run_redteam_scan()`
- 🔄 `eval/scripts/run_eval.py` — добавлена callable функция `run_eval_scan()`
- 🔄 `eval/eval_rag_metrics.py` — `run_eval()` теперь возвращает `Path`
- 🔄 `web/src/app/api/runner/route.ts` — убран spawn, добавлен fetch к FastAPI

## Следующие шаги

1. Добавить polling на фронтенде (redteam/page.tsx, eval/page.tsx)
2. Тестирование интеграции Next.js ↔ FastAPI
3. Деплой на Railway/Render (см. `ARCHITECTURE_REFACTORING.md` Фаза 3)
