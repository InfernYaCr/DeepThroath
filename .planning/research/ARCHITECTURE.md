# ARCHITECTURE.md — RAGAS Integration Architecture

## Компоненты и файлы

```
eval/
├── eval_ragas_metrics.py          # NEW: Python pipeline (аналог eval_rag_metrics.py)
├── custom_metrics/
│   ├── __init__.py                # NEW: экспорт кастомных метрик
│   └── example_metric.py          # NEW: пример кастомной метрики с документацией
└── results/
    └── {timestamp}_ragas/
        └── metrics.json           # NEW: результаты RAGAS (тот же формат что DeepEval)

web/src/app/
├── eval/
│   ├── page.tsx                   # MODIFY: добавить tab switcher (DeepEval | RAGAS)
│   └── ragas/
│       └── page.tsx               # NEW: RAGAS tab содержимое (или inline в eval/page.tsx)
└── api/
    └── eval/
        ├── route.ts               # existing (DeepEval)
        └── ragas/
            └── route.ts           # NEW: RAGAS API endpoint
```

## Data Flow

```
eval/datasets/*.json
      ↓ (read by Python)
eval/eval_ragas_metrics.py
      ↓ (convert to EvaluationDataset)
ragas.evaluate(dataset, metrics, llm)
      ↓ (save results)
eval/results/{timestamp}_ragas/metrics.json
      ↓ (read by Next.js API)
/api/eval/ragas?scan=...
      ↓ (JSON response)
web/src/app/eval/page.tsx (RAGAS tab)
```

## Python Pipeline: eval_ragas_metrics.py

### Входные данные
- Путь к датасету: `eval/datasets/*.json`
- Конфигурация LLM: из `.env` (OPENAI_API_KEY, ANTHROPIC_API_KEY)
- Список метрик: из аргументов командной строки или конфига
- Флаг кастомных метрик: опционально

### Выходные данные
```json
[
  {
    "session_id": "...",
    "category": "...",
    "intent": "...",
    "user_query": "...",
    "actual_answer": "...",
    "expected_answer": "...",
    "faithfulness_score": 0.85,
    "faithfulness_reason": "...",
    "answer_relevancy_score": 0.92,
    "answer_relevancy_reason": "...",
    "context_precision_score": 0.78,
    "context_recall_score": 0.91,
    "answer_correctness_score": 0.88,
    "custom_metric_score": null
  }
]
```

### Структура скрипта (аналог eval_rag_metrics.py)
```python
# 1. Загрузка .env
# 2. Настройка LLM judge (LangchainLLMWrapper)
# 3. Загрузка датасета из JSON
# 4. Конвертация в EvaluationDataset (SingleTurnSample)
# 5. Загрузка метрик (standard + custom)
# 6. ragas.evaluate(dataset, metrics, llm, embeddings)
# 7. Сохранение в eval/results/{timestamp}_ragas/metrics.json
# 8. Вывод в stdout для Next.js subprocess
```

## API Route: /api/eval/ragas/route.ts

Аналог `/api/eval/route.ts`:
- Читает `eval/results/` — фильтрует папки с суффиксом `_ragas`
- Возвращает `{ metrics: [], allScans: [] }`
- Те же поля ответа что и DeepEval API

## UI: Tab Switcher в eval/page.tsx

```
/eval страница
├── Tab: "DeepEval" (существующий контент)
└── Tab: "RAGAS" (новый контент)
    ├── Selector скана (те же scans из /api/eval/ragas)
    ├── Summary cards (avg scores per metric)
    ├── Таблица результатов по записям
    └── Accordion: детали каждой записи
        ├── Вопрос / Ответ / Ground Truth
        ├── Метрики (badges)
        └── Документация по кастомным метрикам (collapsible)
```

## Порядок сборки

1. **Python pipeline** (`eval/eval_ragas_metrics.py`) — ядро, независимо
2. **Custom metrics scaffold** (`eval/custom_metrics/`) — шаблон для пользователя
3. **API route** (`/api/eval/ragas/route.ts`) — читает результаты pipeline
4. **UI tab** (модификация `eval/page.tsx`) — потребляет API

## Результат в eval/results

Папки с суффиксом `_ragas` для отличия от DeepEval:
```
eval/results/
├── 20260417_120000_exp_top_k_10/          # DeepEval (существующий)
│   └── metrics.json
└── 20260417_130000_exp_top_k_10_ragas/    # RAGAS (новый)
    └── metrics.json
```
