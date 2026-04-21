# 🏗️ DeepThroath: Архитектура и План Рефакторинга

> **Дата создания:** 2026-04-21
> **Версия:** 1.0
> **Статус проекта:** 30% готовности к деплою

---

## 📊 Текущая архитектура проекта

```
DeepThroath/
├── 🌐 Frontend (Next.js)
│   └── web/
│       ├── src/app/
│       │   ├── page.tsx                    # Главная страница
│       │   ├── redteam/page.tsx            # Red Team дашборд
│       │   ├── eval/page.tsx               # RAG Evaluation дашборд
│       │   ├── runner/page.tsx             # Provider Comparison
│       │   └── api/                        # ⚠️ ПРОБЛЕМА: 13 API routes с spawn
│       │       ├── run/route.ts            # 🔴 DELETE: spawn redteam
│       │       ├── runner/route.ts         # 🟡 MODIFY: убрать spawn eval
│       │       ├── runner/redteam/route.ts # 🔴 DELETE: дубликат run/
│       │       ├── data/route.ts           # ✅ OK: DuckDB queries
│       │       ├── eval/route.ts           # 🟡 MODIFY: парсинг JSON
│       │       └── ... (8+ других routes)
│       └── tsconfig.json                   # ✅ strict: true
│
├── 🐍 Backend (Python Scripts)
│   ├── src/
│   │   ├── api/                            # 🟢 CREATE: FastAPI микросервис
│   │   │   ├── main.py                     # 🟢 CREATE: FastAPI app
│   │   │   ├── schemas.py                  # 🟢 CREATE: Pydantic модели
│   │   │   ├── runner.py                   # 🟢 CREATE: Background tasks
│   │   │   └── database.py                 # 🟢 CREATE (опционально): SQLite
│   │   ├── red_team/
│   │   │   ├── runner.py                   # 🟡 MODIFY: async wrapper
│   │   │   ├── judges.py                   # ✅ OK
│   │   │   └── attacks.py                  # ✅ OK
│   │   └── dashboard/                      # 🔴 DELETE: Streamlit (9 файлов)
│   │       ├── app.py                      # 🔴 DELETE: дубликат Next.js
│   │       ├── unified_app.py              # 🔴 DELETE
│   │       └── tabs/                       # 🔴 DELETE: весь каталог
│   ├── eval/
│   │   └── scripts/run_eval.py             # 🟡 MODIFY: callable from FastAPI
│   └── scripts/
│       └── run_redteam.py                  # 🟡 MODIFY: callable from FastAPI
│
├── 📦 Конфигурация
│   ├── requirements.txt                    # 🟡 MODIFY: добавить fastapi, uvicorn
│   ├── pyproject.toml                      # 🟢 CREATE: mypy, black, ruff
│   └── docker-compose.yml                  # 🟢 CREATE (фаза 2): деплой
│
└── 📊 Результаты
    ├── results/                            # Red Team: Parquet
    └── eval/results/                       # RAG Eval: JSON

```

---

## 🚨 Критические проблемы

### 1. **child_process.spawn блокирует деплой** 🔴

**Файлы с проблемой:**
- `web/src/app/api/run/route.ts:15` — синхронный spawn
- `web/src/app/api/runner/route.ts:38` — асинхронный spawn + временные файлы
- `web/src/app/api/runner/redteam/route.ts:45` — дубликат логики

**Почему это проблема:**
- На Vercel/Netlify таймаут API route = 10-60 сек
- Долгие LLM тесты (5-10 мин) = 504 Gateway Timeout
- Serverless убивает фоновые процессы после HTTP response

**Решение:**
```typescript
// ❌ СТАРЫЙ КОД (web/src/app/api/run/route.ts)
const pythonProcess = spawn('python', ['scripts/run_redteam.py', '--config', configPath]);
pythonProcess.on('close', (code) => { /* блокируем поток */ });

// ✅ НОВЫЙ КОД
const response = await fetch('http://localhost:8000/api/runner/redteam', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(config),
});
const { job_id } = await response.json();
return NextResponse.json({ job_id, status: 'pending' });
```

---

### 2. **Дублирование Streamlit дашбордов** 🔴

**Файлы к удалению (2689 строк мусора):**
```bash
src/dashboard/app.py                    # 309 строк
src/dashboard/unified_app.py            # 487 строк
src/dashboard/tabs/quality.py           # 612 строк
src/dashboard/tabs/security.py          # 724 строк
src/dashboard/tabs/summary.py           # 289 строк
src/dashboard/tabs/attack_analysis.py
src/dashboard/tabs/comparative.py
src/dashboard/components/charts.py
src/dashboard/utils/data_loader.py
```

**Почему удалять безопасно:**
- Next.js дублирует весь функционал:
  - `web/src/app/redteam/page.tsx` заменяет `tabs/security.py`
  - `web/src/app/eval/page.tsx` заменяет `tabs/quality.py`
- Streamlit невозможно задеплоить вместе с Next.js на serverless

**Действие:**
```bash
rm -rf src/dashboard/
# Удалить из requirements.txt:
# - streamlit==1.41.0
# - plotly==5.18.0 (если не используется в Next.js)
```

---

### 3. **Временные конфиг-файлы вместо HTTP payload** 🟡

**Проблемные места:**
```typescript
// web/src/app/api/runner/route.ts:29
const tmpConfigFile = `.tmp_api_config_${randomUUID()}.json`;
fs.writeFileSync(tmpConfigFile, JSON.stringify(config));

// web/src/app/api/runner/redteam/route.ts:41
const tmpRedteamConfig = `.tmp_redteam_api_config_${randomUUID()}.json`;
```

**Проблемы:**
- Файлы остаются при крашах (нет cleanup в `finally`)
- Риск утечки конфигов (API ключи в plaintext)
- Не работает в serverless (read-only filesystem)

**Решение:** Передавать конфиг через HTTP body к FastAPI

---

## ✅ План рефакторинга по приоритетам

### 🔥 Фаза 1: Критичные изменения (1 неделя)

#### **Задача 1.1: Создать FastAPI микросервис** (5-7 дней)

**Создать файлы:**

1. **`src/api/main.py`** — FastAPI приложение
```python
"""
FastAPI микросервис для долгих LLM задач.
Заменяет child_process.spawn из Next.js API routes.
"""
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import RedTeamRequest, EvalRequest, JobResponse, JobStatus
from .runner import run_redteam_background, run_eval_background
import uuid

app = FastAPI(
    title="DeepThroath API",
    version="1.0.0",
    description="API для Red Team и RAG Evaluation"
)

# CORS для Next.js на localhost:3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-vercel-domain.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory хранилище состояний задач (MVP)
# TODO: Заменить на SQLite в Фазе 2
jobs: dict[str, JobStatus] = {}

@app.post("/api/runner/redteam", response_model=JobResponse, tags=["Red Team"])
async def create_redteam_job(
    request: RedTeamRequest,
    background_tasks: BackgroundTasks
):
    """
    Запустить Red Team сканирование в фоне.
    Возвращает job_id для отслеживания прогресса.
    """
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id=job_id, status="pending", progress=0)

    # Запуск в фоне (не блокирует HTTP response)
    background_tasks.add_task(
        run_redteam_background,
        job_id=job_id,
        config=request,
        jobs_dict=jobs
    )

    return JobResponse(job_id=job_id, status="pending")

@app.post("/api/runner/eval", response_model=JobResponse, tags=["RAG Evaluation"])
async def create_eval_job(
    request: EvalRequest,
    background_tasks: BackgroundTasks
):
    """Запустить RAG Evaluation в фоне"""
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(job_id=job_id, status="pending", progress=0)

    background_tasks.add_task(
        run_eval_background,
        job_id=job_id,
        config=request,
        jobs_dict=jobs
    )

    return JobResponse(job_id=job_id, status="pending")

@app.get("/api/jobs/{job_id}/status", response_model=JobStatus, tags=["Jobs"])
async def get_job_status(job_id: str):
    """
    Получить статус задачи по ID.
    Next.js опрашивает этот эндпоинт каждые 3 секунды (polling).
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return jobs[job_id]

@app.get("/api/jobs", tags=["Jobs"])
async def list_jobs():
    """Список всех задач (для истории прогонов)"""
    return list(jobs.values())

@app.get("/health")
async def health_check():
    """Health check для Docker/Kubernetes"""
    return {"status": "healthy", "service": "deepthroath-api"}
```

**Агент-разработчик, обрати внимание:**
- Используй `BackgroundTasks` для долгих задач
- `jobs: dict` — временное решение для MVP, замени на SQLite в Фазе 2
- CORS должен включать production домен при деплое
- Каждый эндпоинт должен иметь docstring для OpenAPI docs

---

2. **`src/api/schemas.py`** — Pydantic модели
```python
"""
Pydantic схемы для валидации запросов и ответов.
Заменяют отсутствующую валидацию в Next.js API routes.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class RedTeamRequest(BaseModel):
    """Запрос на запуск Red Team сканирования"""
    target: str = Field(
        ...,
        description="Провайдер модели: openai:gpt-4o, anthropic:claude-sonnet-4, etc.",
        examples=["openai:gpt-4o"]
    )
    num_attacks: int = Field(
        10,
        ge=1,
        le=1000,
        description="Количество атак для генерации"
    )
    attack_types: list[str] = Field(
        default_factory=list,
        description="Типы атак: jailbreak, prompt_injection, pii_leak, etc."
    )
    system_prompt: str | None = Field(
        None,
        description="Кастомный system prompt для модели"
    )

    @field_validator('target')
    @classmethod
    def validate_target(cls, v: str) -> str:
        valid_providers = ['openai', 'anthropic', 'deepseek', 'gemini']
        provider = v.split(':')[0]
        if provider not in valid_providers:
            raise ValueError(f"Неизвестный провайдер: {provider}")
        return v

class EvalRequest(BaseModel):
    """Запрос на запуск RAG Evaluation"""
    dataset: str = Field(..., description="Имя датасета из eval/datasets/")
    model: str = Field(..., description="Модель для генерации ответов")
    metrics: list[str] = Field(
        default_factory=lambda: ["answer_relevancy", "faithfulness", "contextual_precision"],
        description="DeepEval метрики для оценки"
    )
    n_samples: int = Field(50, ge=1, le=500, description="Количество примеров")

class JobResponse(BaseModel):
    """Ответ при создании задачи"""
    job_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    message: str = "Job created successfully"

class JobStatus(BaseModel):
    """Статус выполнения задачи"""
    job_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: int = Field(0, ge=0, le=100, description="Прогресс в процентах")
    results_path: str | None = Field(None, description="Путь к результатам при завершении")
    error: str | None = Field(None, description="Сообщение об ошибке при провале")
    created_at: str | None = None
    completed_at: str | None = None
```

**Агент-разработчик, обрати внимание:**
- `field_validator` защищает от невалидных провайдеров
- `ge/le` ограничивают диапазоны (num_attacks: 1-1000)
- Docstrings попадут в Swagger UI автоматически

---

3. **`src/api/runner.py`** — Фоновые задачи
```python
"""
Обертки для запуска долгих Python скриптов в фоне.
Адаптирует существующие scripts/run_redteam.py под async.
"""
import asyncio
from datetime import datetime
from .schemas import RedTeamRequest, EvalRequest, JobStatus
import traceback

async def run_redteam_background(
    job_id: str,
    config: RedTeamRequest,
    jobs_dict: dict[str, JobStatus]
):
    """
    Фоновый запуск Red Team сканирования.
    Обновляет jobs_dict по мере выполнения.
    """
    try:
        # Обновляем статус
        jobs_dict[job_id].status = "running"
        jobs_dict[job_id].created_at = datetime.now().isoformat()

        # Импортируем существующую логику
        # ВАЖНО: Адаптировать run_redteam.py для вызова как функции
        from scripts.run_redteam import main as redteam_main

        # Запускаем в thread pool (блокирующий код)
        results_path = await asyncio.to_thread(
            redteam_main,
            target=config.target,
            num_attacks=config.num_attacks,
            attack_types=config.attack_types,
            system_prompt=config.system_prompt
        )

        # Успех
        jobs_dict[job_id].status = "completed"
        jobs_dict[job_id].progress = 100
        jobs_dict[job_id].results_path = str(results_path)
        jobs_dict[job_id].completed_at = datetime.now().isoformat()

    except Exception as e:
        # Ошибка
        jobs_dict[job_id].status = "failed"
        jobs_dict[job_id].error = f"{type(e).__name__}: {str(e)}"
        jobs_dict[job_id].completed_at = datetime.now().isoformat()

        # Логируем полный traceback
        print(f"[ERROR] Job {job_id} failed:")
        traceback.print_exc()

async def run_eval_background(
    job_id: str,
    config: EvalRequest,
    jobs_dict: dict[str, JobStatus]
):
    """Фоновый запуск RAG Evaluation"""
    try:
        jobs_dict[job_id].status = "running"
        jobs_dict[job_id].created_at = datetime.now().isoformat()

        from eval.scripts.run_eval import main as eval_main

        results_path = await asyncio.to_thread(
            eval_main,
            dataset=config.dataset,
            model=config.model,
            metrics=config.metrics,
            n_samples=config.n_samples
        )

        jobs_dict[job_id].status = "completed"
        jobs_dict[job_id].progress = 100
        jobs_dict[job_id].results_path = str(results_path)
        jobs_dict[job_id].completed_at = datetime.now().isoformat()

    except Exception as e:
        jobs_dict[job_id].status = "failed"
        jobs_dict[job_id].error = str(e)
        traceback.print_exc()
```

**Агент-разработчик, обрати внимание:**
- `asyncio.to_thread` — для блокирующих Python функций
- Нужно адаптировать `scripts/run_redteam.py` чтобы main() возвращал путь к результатам
- `traceback.print_exc()` — для дебага ошибок
- TODO: Добавить callback для обновления progress (0-100%)

---

4. **Модифицировать `scripts/run_redteam.py`**

**Текущий код (CLI):**
```python
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # ... парсинг аргументов
    main(args)
```

**Новый код (callable function):**
```python
def main(
    target: str,
    num_attacks: int = 10,
    attack_types: list[str] | None = None,
    system_prompt: str | None = None
) -> Path:
    """
    Запуск Red Team сканирования.

    Returns:
        Path: Путь к файлу с результатами (results/latest.parquet)
    """
    # ... существующая логика

    # В конце:
    results_path = Path("results/latest.parquet")
    return results_path

# CLI обертка
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--num-attacks", type=int, default=10)
    parser.add_argument("--attack-types", nargs="+", default=[])
    parser.add_argument("--system-prompt", default=None)
    args = parser.parse_args()

    results = main(
        target=args.target,
        num_attacks=args.num_attacks,
        attack_types=args.attack_types,
        system_prompt=args.system_prompt
    )
    print(f"Results saved to: {results}")
```

**Агент-разработчик, обрати внимание:**
- `main()` должна возвращать `Path` к результатам
- CLI-обертка остается для ручного запуска
- Аналогично для `eval/scripts/run_eval.py`

---

5. **Обновить `requirements.txt`**
```diff
# Существующие зависимости
anthropic==0.42.0
openai==1.59.7
deepeval==1.5.2
+
+# FastAPI микросервис
+fastapi==0.115.6
+uvicorn[standard]==0.34.0
+python-multipart==0.0.20  # для file uploads (если понадобится)
+
+# Опционально для Фазы 2
+# sqlmodel==0.0.22  # для SQLite job tracking
+
+# Линтеры и типизация (Фаза 2)
+# mypy==1.14.0
+# black==24.10.0
+# ruff==0.8.4
```

---

#### **Задача 1.2: Переписать Next.js API routes** (1 день)

**Файл: `web/src/app/api/runner/route.ts`**

**❌ СТАРЫЙ КОД (с spawn):**
```typescript
// УДАЛИТЬ ЭТОТ КОД
const tmpConfigFile = `.tmp_api_config_${randomUUID()}.json`;
fs.writeFileSync(tmpConfigFile, JSON.stringify(config));

const pythonProcess = spawn('python', ['eval/scripts/run_eval.py', '--config', tmpConfigFile]);

pythonProcess.on('close', (code) => {
  // Блокирует поток
});
```

**✅ НОВЫЙ КОД (с fetch к FastAPI):**
```typescript
import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const config = await request.json();

    // Валидация (опционально: можно добавить zod)
    if (!config.dataset || !config.model) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // Запрос к FastAPI микросервису
    const response = await fetch('http://localhost:8000/api/runner/eval', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        dataset: config.dataset,
        model: config.model,
        metrics: config.metrics || ['answer_relevancy', 'faithfulness'],
        n_samples: config.n_samples || 50,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(
        { error: error.detail || 'Failed to create job' },
        { status: response.status }
      );
    }

    const { job_id, status } = await response.json();

    return NextResponse.json({
      job_id,
      status,
      message: 'Evaluation started. Poll /api/jobs/{job_id}/status for updates.',
    });

  } catch (error) {
    console.error('Error creating eval job:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

**Агент-разработчик, обрати внимание:**
- Удалить все `spawn`, `fs.writeFileSync`, `randomUUID()` для временных файлов
- URL FastAPI: в деплое заменить `localhost:8000` на переменную окружения `NEXT_PUBLIC_API_URL`
- Добавить обработку ошибок (status 400/500)

---

**Создать новый файл: `web/src/app/api/jobs/[jobId]/status/route.ts`**

```typescript
import { NextResponse } from 'next/server';

export async function GET(
  request: Request,
  { params }: { params: { jobId: string } }
) {
  try {
    const { jobId } = params;

    // Проксируем запрос к FastAPI
    const response = await fetch(`http://localhost:8000/api/jobs/${jobId}/status`);

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Job not found' },
        { status: 404 }
      );
    }

    const status = await response.json();
    return NextResponse.json(status);

  } catch (error) {
    console.error('Error fetching job status:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

**Агент-разработчик, обрати внимание:**
- Это BFF (Backend-for-Frontend) паттерн — Next.js проксирует к FastAPI
- Можно добавить кеширование на стороне Next.js (Redis/Vercel KV)

---

**Файлы к удалению:**
```bash
# УДАЛИТЬ полностью (дубликаты)
web/src/app/api/run/route.ts                # 38 строк
web/src/app/api/runner/redteam/route.ts     # 77 строк
```

**Файлы к модификации:**
```bash
# ИЗМЕНИТЬ (убрать spawn)
web/src/app/api/runner/route.ts             # Для eval
# Создать аналогичный для redteam, если нужен отдельный роут
```

---

#### **Задача 1.3: Добавить polling на фронтенде** (1 день)

**Файл: `web/src/app/redteam/page.tsx`**

**Добавить хук для polling:**
```typescript
'use client';

import { useState, useEffect } from 'react';

interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  results_path?: string;
  error?: string;
}

export default function RedTeamPage() {
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);

  // Запуск теста
  const handleStartTest = async (config: any) => {
    try {
      const res = await fetch('/api/runner', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: 'redteam', ...config }),
      });

      const { job_id } = await res.json();
      setJobId(job_id);
      setIsPolling(true);
    } catch (error) {
      console.error('Failed to start test:', error);
    }
  };

  // Polling каждые 3 секунды
  useEffect(() => {
    if (!jobId || !isPolling) return;

    const pollStatus = async () => {
      try {
        const res = await fetch(`/api/jobs/${jobId}/status`);
        const data = await res.json();
        setStatus(data);

        // Остановить polling если завершено
        if (data.status === 'completed' || data.status === 'failed') {
          setIsPolling(false);
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    };

    // Первый запрос сразу
    pollStatus();

    // Затем каждые 3 секунды
    const interval = setInterval(pollStatus, 3000);

    return () => clearInterval(interval);
  }, [jobId, isPolling]);

  return (
    <div>
      <button onClick={() => handleStartTest({ /* config */ })}>
        Run Red Team Test
      </button>

      {status && (
        <div>
          <h3>Status: {status.status}</h3>
          <ProgressBar value={status.progress} />

          {status.status === 'completed' && (
            <a href={`/results?path=${status.results_path}`}>
              View Results
            </a>
          )}

          {status.status === 'failed' && (
            <p className="text-red-500">Error: {status.error}</p>
          )}
        </div>
      )}
    </div>
  );
}
```

**Агент-разработчик, обрати внимание:**
- Polling интервал: 3 секунды (не слишком часто для production)
- Cleanup `clearInterval` в useEffect return
- Можно улучшить: WebSockets для real-time (Фаза 3)

---

#### **Задача 1.4: Удалить Streamlit** (2 часа)

**Команды:**
```bash
# Удалить каталог
rm -rf src/dashboard/

# Обновить requirements.txt
# Удалить строки:
# streamlit==1.41.0
# plotly==5.18.0 (если не используется в Next.js)
```

**Проверка зависимостей:**
```bash
# Убедиться что plotly не используется в Next.js
grep -r "plotly" web/src/
# Если нет совпадений — можно удалять из requirements
```

**Агент-разработчик, обрати внимание:**
- Streamlit использовал порт 8501 — освобождается для других сервисов
- После удаления остается только Next.js как единственный UI

---

### 🟡 Фаза 2: Улучшения качества (1 неделя)

#### **Задача 2.1: Добавить mypy и типизацию** (4 часа)

**Создать: `pyproject.toml`**
```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true

# Игнорировать библиотеки без типов
[[tool.mypy.overrides]]
module = "deepeval.*"
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "duckdb.*"
ignore_missing_imports = true

[tool.black]
line-length = 100
target-version = ['py311']
extend-exclude = '''
/(
  | venv
  | .venv
  | node_modules
)/
'''

[tool.ruff]
line-length = 100
target-version = "py311"
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "UP",  # pyupgrade
]
```

**Обновить ключевые файлы с return types:**

```python
# src/red_team/runner.py
def create_anthropic_callback(
    model: str,
    system_prompt: str,
    api_key: str | None = None,
) -> callable:  # 🟢 Добавить return type
    """..."""
    pass

# eval/scripts/run_eval.py
def load_dataset(dataset_name: str) -> list[dict[str, Any]]:  # 🟢
    """..."""
    pass
```

**Запуск проверки:**
```bash
mypy src/ eval/ --strict
black src/ eval/ --check
ruff check src/ eval/
```

---

#### **Задача 2.2: SQLite для job tracking** (2 дня, опционально)

**Когда делать:** После MVP с in-memory storage

**Создать: `src/api/database.py`**
```python
from sqlmodel import SQLModel, Field, create_engine, Session, select
from datetime import datetime
from pathlib import Path

class JobRecord(SQLModel, table=True):
    """История всех прогонов"""
    __tablename__ = "jobs"

    id: str = Field(primary_key=True)
    status: str  # pending | running | completed | failed
    job_type: str  # redteam | eval
    config: str  # JSON сериализованный RedTeamRequest/EvalRequest
    progress: int = Field(default=0)
    results_path: str | None = Field(default=None)
    error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = Field(default=None)

# Создание БД
db_path = Path("jobs.db")
engine = create_engine(f"sqlite:///{db_path}")
SQLModel.metadata.create_all(engine)

def save_job(job: JobRecord) -> None:
    """Сохранить задачу в БД"""
    with Session(engine) as session:
        session.add(job)
        session.commit()

def get_job(job_id: str) -> JobRecord | None:
    """Получить задачу по ID"""
    with Session(engine) as session:
        statement = select(JobRecord).where(JobRecord.id == job_id)
        return session.exec(statement).first()

def update_job(job_id: str, **kwargs) -> None:
    """Обновить поля задачи"""
    with Session(engine) as session:
        statement = select(JobRecord).where(JobRecord.id == job_id)
        job = session.exec(statement).first()
        if job:
            for key, value in kwargs.items():
                setattr(job, key, value)
            session.add(job)
            session.commit()

def list_jobs(limit: int = 100) -> list[JobRecord]:
    """Список всех задач (для истории)"""
    with Session(engine) as session:
        statement = select(JobRecord).order_by(JobRecord.created_at.desc()).limit(limit)
        return list(session.exec(statement).all())
```

**Модифицировать `src/api/main.py`:**
```python
# Вместо in-memory dict
from .database import save_job, get_job, update_job, list_jobs, JobRecord

@app.post("/api/runner/redteam")
async def create_redteam_job(request: RedTeamRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())

    # Сохранить в БД
    job = JobRecord(
        id=job_id,
        status="pending",
        job_type="redteam",
        config=request.model_dump_json()
    )
    save_job(job)

    background_tasks.add_task(run_redteam_background, job_id, request)
    return JobResponse(job_id=job_id, status="pending")

@app.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404)
    return job
```

**Агент-разработчик, обрати внимание:**
- SQLite файл `jobs.db` должен быть в `.gitignore`
- Можно добавить эндпоинт `/api/jobs/history` для таблицы прошлых запусков
- В production: заменить SQLite на PostgreSQL (Railway/Render)

---

### 🟢 Фаза 3: Production-ready (2-3 недели)

#### **Задача 3.1: Docker Compose** (3 дня)

**Создать: `Dockerfile.api`** (для FastAPI)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Копировать зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копировать код
COPY src/ ./src/
COPY eval/ ./eval/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Запуск
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Создать: `docker-compose.yml`**
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./results:/app/results  # Монтировать результаты
      - ./jobs.db:/app/jobs.db  # Персистентная БД
    restart: unless-stopped

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:8000
    depends_on:
      - api
    restart: unless-stopped

  # Опционально: Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - web
      - api
```

**Запуск:**
```bash
docker-compose up -d
# Доступ: http://localhost (Nginx) → http://localhost:3000 (Next.js) → http://localhost:8000 (FastAPI)
```

---

#### **Задача 3.2: Pre-commit hooks** (1 час)

**Создать: `.pre-commit-config.yaml`**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.14.0
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, sqlmodel]
```

**Установка:**
```bash
pip install pre-commit
pre-commit install
```

**Агент-разработчик, обрати внимание:**
- Хуки запускаются автоматически при `git commit`
- Можно добавить prettier для TypeScript (Next.js)

---

## 📊 Чек-лист выполнения

### Фаза 1: Критичные изменения ✅

- [ ] **1.1** Создать FastAPI микросервис
  - [ ] `src/api/main.py` — FastAPI app
  - [ ] `src/api/schemas.py` — Pydantic модели
  - [ ] `src/api/runner.py` — Background tasks
  - [ ] Модифицировать `scripts/run_redteam.py` (callable function)
  - [ ] Модифицировать `eval/scripts/run_eval.py` (callable function)
  - [ ] Обновить `requirements.txt` (fastapi, uvicorn)

- [ ] **1.2** Переписать Next.js API routes
  - [ ] Обновить `web/src/app/api/runner/route.ts` (убрать spawn)
  - [ ] Создать `web/src/app/api/jobs/[jobId]/status/route.ts`
  - [ ] Удалить `web/src/app/api/run/route.ts`
  - [ ] Удалить `web/src/app/api/runner/redteam/route.ts`

- [ ] **1.3** Добавить polling на фронтенде
  - [ ] Обновить `web/src/app/redteam/page.tsx` (useEffect polling)
  - [ ] Обновить `web/src/app/eval/page.tsx` (аналогично)
  - [ ] Добавить ProgressBar компонент

- [ ] **1.4** Удалить Streamlit
  - [ ] `rm -rf src/dashboard/`
  - [ ] Удалить `streamlit` из `requirements.txt`

### Фаза 2: Улучшения качества ⏳

- [ ] **2.1** Добавить mypy и типизацию
  - [ ] Создать `pyproject.toml`
  - [ ] Добавить return types в `src/red_team/runner.py`
  - [ ] Добавить return types в `eval/scripts/run_eval.py`
  - [ ] Запустить `mypy --strict` без ошибок

- [ ] **2.2** SQLite для job tracking (опционально)
  - [ ] Создать `src/api/database.py`
  - [ ] Модифицировать `src/api/main.py` (использовать БД)
  - [ ] Добавить эндпоинт `/api/jobs/history`

### Фаза 3: Production-ready 🟢

- [ ] **3.1** Docker Compose
  - [ ] Создать `Dockerfile.api`
  - [ ] Создать `docker-compose.yml`
  - [ ] Протестировать `docker-compose up`

- [ ] **3.2** Pre-commit hooks
  - [ ] Создать `.pre-commit-config.yaml`
  - [ ] Установить `pre-commit install`

---

## 🚀 Команды для запуска

### Локальная разработка

**Терминал 1: FastAPI**
```bash
uvicorn src.api.main:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

**Терминал 2: Next.js**
```bash
cd web/
npm run dev
# UI: http://localhost:3000
```

### Production (Docker)

```bash
docker-compose up -d
docker-compose logs -f  # Логи
docker-compose down     # Остановка
```

---

## 🎯 Итоговая оценка готовности

| Компонент | До рефакторинга | После Фазы 1 | После Фазы 2 | После Фазы 3 |
|-----------|-----------------|--------------|--------------|--------------|
| **API слой** | 🔴 2/10 (spawn) | 🟢 8/10 (FastAPI) | 🟢 9/10 (SQLite) | 🟢 10/10 (Docker) |
| **Типизация** | 🟡 5/10 (частичная) | 🟡 6/10 | 🟢 9/10 (mypy) | 🟢 10/10 (hooks) |
| **Дублирование** | 🔴 3/10 (Streamlit) | 🟢 9/10 (удален) | 🟢 9/10 | 🟢 10/10 |
| **Деплой-готовность** | 🔴 1/10 (fail) | 🟢 8/10 (Railway) | 🟢 9/10 | 🟢 10/10 (K8s ready) |

**Общая оценка:**
- До рефакторинга: **30%**
- После Фазы 1: **80%** ✅ Готов к деплою
- После Фазы 2: **90%** ✅ Production-ready
- После Фазы 3: **100%** ✅ Enterprise-grade

---

## 📝 Важные замечания для агента-разработчика

### Приоритеты:
1. **Фаза 1 — критична** для деплоя (1 неделя)
2. **Фаза 2 — важна** для качества кода (1 неделя)
3. **Фаза 3 — опциональна** для энтерпрайз (2-3 недели)

### Риски:
- **Адаптация `run_redteam.py`**: может потребоваться рефакторинг логики
- **Долгие тесты**: polling должен обрабатывать задачи до 10+ минут
- **CORS в production**: не забыть добавить production URL в `allow_origins`

### Следующие шаги:
1. Начни с **FastAPI микросервиса** (`src/api/main.py`)
2. Затем **адаптируй Python скрипты** (callable functions)
3. Переписывай **Next.js routes** последовательно (сначала eval, потом redteam)
4. Тестируй каждый этап локально перед деплоем

---

**Версия документа:** 1.0
**Последнее обновление:** 2026-04-21
**Автор:** Claude Sonnet 4.5 (QA Analysis Agent)
