# PITFALLS.md — RAGAS Integration Pitfalls

## 1. Конфликт зависимостей langchain

**Признак:** `ImportError: cannot import name 'ChatOpenAI' from 'langchain'`

**Причина:** RAGAS требует `langchain-openai` (отдельный пакет), но в проекте его нет. Старый `langchain` (монолит) конфликтует с новым разделённым API.

**Профилактика:**
```bash
pip install ragas langchain-openai langchain-core
# НЕ устанавливать просто langchain без версии
```
**Фаза:** Phase 1 (Python pipeline)

---

## 2. Asyncio event loop в subprocess

**Признак:** `RuntimeError: This event loop is already running` или скрипт зависает при запуске из Next.js.

**Причина:** RAGAS использует `asyncio.run()` внутри. При запуске через subprocess Python event loop создаётся правильно, но на macOS может быть конфликт с `ProactorEventLoop`.

**Профилактика:**
```python
import asyncio
import sys

if sys.platform == "darwin":
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())

# В main():
asyncio.run(main_async())
```
**Фаза:** Phase 1 (Python pipeline)

---

## 3. Missing retrieval_context в датасете

**Признак:** `ContextPrecision` и `ContextRecall` возвращают `NaN` или ошибку.

**Причина:** Датасет `eval/datasets/*.json` не содержит поле `retrieval_context`. Контекст хранится в исходном top_k файле, который уже не доступен.

**Профилактика:**
- Pipeline должен принимать top_k JSON как входной файл (как DeepEval)
- Либо graceful skip контекстных метрик если контекст отсутствует
- Добавить проверку: если `retrieved_contexts` пустой — пропустить ContextPrecision/ContextRecall

**Фаза:** Phase 1 (конвертер датасета)

---

## 4. AnswerRelevancy требует embeddings

**Признак:** `ValueError: embeddings are required for AnswerRelevancy`

**Причина:** AnswerRelevancy использует semantic similarity через embeddings, не только LLM.

**Профилактика:**
```python
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import OpenAIEmbeddings

embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings())
result = evaluate(dataset, metrics=[AnswerRelevancy()], llm=llm, embeddings=embeddings)
```
**Фаза:** Phase 1 (Python pipeline)

---

## 5. RAGAS API v0.1 vs v0.2 (vibrantlabsai fork)

**Признак:** `from ragas import Dataset` → `ImportError` (старый API)

**Причина:** vibrantlabsai fork может использовать старый API ragas v0.1 где `Dataset` вместо `EvaluationDataset`.

**Профилактика:**
```python
# Проверить версию после установки:
import ragas; print(ragas.__version__)

# v0.1 (старый):
from ragas import Dataset
dataset = Dataset.from_list([{"question": ..., "answer": ..., "contexts": [...], "ground_truth": ...}])

# v0.2+ (новый):
from ragas import EvaluationDataset
from ragas.dataset_schema import SingleTurnSample
```
Писать с проверкой версии или поддерживать оба API.

**Фаза:** Phase 1

---

## 6. Rate limiting LLM судьи

**Признак:** `RateLimitError` на больших датасетах.

**Причина:** RAGAS по умолчанию запускает метрики параллельно для каждого sample.

**Профилактика:**
```python
# Ограничить параллелизм через RAGAS конфиг:
from ragas import RunConfig
run_config = RunConfig(max_workers=2, max_wait=120)
result = evaluate(dataset, metrics=..., run_config=run_config)
```
**Фаза:** Phase 1

---

## 7. Tab switcher сломает существующий eval

**Признак:** Добавление tab switcher в `eval/page.tsx` сломает существующий DeepEval UI.

**Причина:** Неправильная интеграция state management для активной вкладки.

**Профилактика:**
- Сначала извлечь существующий контент в компонент `DeepEvalTab`
- Затем добавить `RagasTab` рядом
- Tab state управляется через `useState<'deepeval' | 'ragas'>`
- Existing API calls остаются нетронутыми

**Фаза:** Phase 3 (UI)

---

## 8. Results folder naming collision

**Признак:** `/api/eval` показывает RAGAS результаты вместо DeepEval.

**Причина:** Если RAGAS результаты сохраняются в той же папке что DeepEval.

**Профилактика:**
- RAGAS сохраняет в `{timestamp}_ragas/metrics.json`
- `/api/eval/ragas` фильтрует только папки с `_ragas` суффиксом
- `/api/eval` игнорирует папки с `_ragas` суффиксом

**Фаза:** Phase 2 (API route)
