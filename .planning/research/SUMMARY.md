# SUMMARY.md — Research Synthesis: RAGAS Integration

## Key Findings

**Stack:** `pip install ragas langchain-openai langchain-core` — RAGAS v0.2+ с `EvaluationDataset` API. LLM judge через `LangchainLLMWrapper(ChatOpenAI(...))`. AnswerRelevancy требует отдельные embeddings.

**Table Stakes:** Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall, AnswerCorrectness — все 5 метрик в v1.

**Watch Out For:**
1. `langchain-openai` не установлен — добавить в requirements.txt
2. `retrieved_contexts` может отсутствовать в датасете — graceful skip для контекстных метрик
3. vibrantlabsai fork может быть v0.1 API (старый `Dataset` вместо `EvaluationDataset`) — проверить версию
4. Tab switcher должен извлечь существующий DeepEval UI в компонент, не ломать его

## Архитектурное решение

**Паттерн**: точно такой же как DeepEval — Python subprocess + JSON results + Next.js API + UI tab.

**Порядок сборки**: Python pipeline → API route → UI tab (3 независимые фазы).

**Ключевое отличие от DeepEval**: RAGAS нужны `langchain-*` зависимости и embeddings для AnswerRelevancy. Форматы результатов выровнять с DeepEval для единообразия UI.

## Требования к датасету

Входной файл должен содержать `retrieval_context` (список чанков). Если используется `eval/datasets/*.json` без контекста — контекстные метрики (ContextPrecision, ContextRecall) будут пропущены. Полный прогон требует top_k JSON как у DeepEval.

## Кастомные метрики

Subclass `MetricWithLLM + SingleTurnMetric`, реализовать `_single_turn_ascore`. Размещать в `eval/custom_metrics/`. Документацию встроить в UI как collapsible секцию с копируемым шаблоном.
