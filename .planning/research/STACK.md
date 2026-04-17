# STACK.md — RAGAS Integration

## Пакет RAGAS

```bash
# Upstream (рекомендуется)
pip install ragas

# Fork от vibrantlabsai (может иметь иной API)
pip install git+https://github.com/vibrantlabsai/ragas.git
```

**Текущий статус (2025):** ragas==0.2.x — стабильная ветка. API изменился с v0.1 (старый `evaluate(dataset, metrics)` стал `evaluate(dataset=..., metrics=...)` с `EvaluationDataset`).

### Зависимости ragas (критичные конфликты)

| Пакет | Требуется ragas | Текущий в проекте | Статус |
|-------|----------------|-------------------|--------|
| openai | >=1.0 | 2.30.0 | ✓ совместимо |
| langchain-openai | >=0.1 | отсутствует | ⚠ нужно добавить |
| langchain-core | >=0.2 | отсутствует | ⚠ нужно добавить |
| pydantic | >=2.0 | 2.12.5 | ✓ совместимо |
| numpy | >=1.24 | транзитивно | ✓ |

**Добавить в requirements.txt:**
```
ragas>=0.2.0
langchain-openai>=0.1.0
langchain-core>=0.2.0
```

## Формат данных RAGAS

RAGAS использует `EvaluationDataset` из `SingleTurnSample`:

```python
from ragas import EvaluationDataset
from ragas.dataset_schema import SingleTurnSample

sample = SingleTurnSample(
    user_input="вопрос пользователя",          # question
    response="фактический ответ",              # actual_output
    retrieved_contexts=["чанк1", "чанк2"],     # retrieval_context (list)
    reference="ожидаемый ответ (ground truth)" # expected_output
)
dataset = EvaluationDataset(samples=[sample, ...])
```

### Маппинг из существующего формата

| Поле датасета (DeepEval) | Поле RAGAS | Примечание |
|--------------------------|-----------|------------|
| `question` | `user_input` | обязательно |
| `actual_output` / `actual_answer` | `response` | обязательно |
| `retrieval_context` (list) | `retrieved_contexts` | обязательно для контекстных метрик |
| `expected_output` | `reference` | нужен для ContextRecall, AnswerCorrectness |

**Текущий формат eval/results JSON:**
```
session_id, top_k, category, intent, user_query, actual_answer, 
answer_relevancy_score, faithfulness_score, contextual_precision_score, contextual_recall_score
```

**Входной датасет (eval/datasets/*.json):**
```
id, category, question, expected_output, actual_output, _source_session, _source_category
```
*Поле retrieval_context берётся из source file (top_k JSON), не из dataset.*

## LLM Judge настройка

```python
from ragas.llms import LangchainLLMWrapper
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

# OpenAI (рекомендуется)
llm = LangchainLLMWrapper(ChatOpenAI(
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")  # дляастарте через прокси
))

# Anthropic
llm = LangchainLLMWrapper(ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    api_key=os.getenv("ANTHROPIC_API_KEY")
))

# Embeddings (нужны для AnswerRelevancy)
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import OpenAIEmbeddings
embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(
    model="text-embedding-3-small"
))
```

## Запуск evaluate

```python
from ragas import evaluate
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision, ContextRecall

result = evaluate(
    dataset=dataset,
    metrics=[Faithfulness(), AnswerRelevancy(), ContextPrecision(), ContextRecall()],
    llm=llm,
    embeddings=embeddings,
    raise_exceptions=False,  # не падать при ошибке одной метрики
)

# Получить DataFrame
df = result.to_pandas()
scores_dict = result.scores  # список dict по каждому sample
```

## Async в subprocess

RAGAS использует asyncio. При запуске через subprocess нужен явный event loop:

```python
import asyncio

if __name__ == "__main__":
    # Python 3.10+ на macOS может требовать:
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    asyncio.run(main())
```

## Конфиденс

- **Пакет ragas**: высокий — стабильный pip install
- **API EvaluationDataset**: высокий — документировано в ragas docs
- **LangchainLLMWrapper**: высокий — основной паттерн интеграции
- **vibrantlabsai fork**: средний — может иметь отличия от upstream
