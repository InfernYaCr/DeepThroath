# FEATURES.md — RAGAS Metrics & Custom Metrics

## Стандартные метрики RAGAS

### Retrieval метрики (нужен retrieved_contexts)

| Метрика | Класс | Ground Truth | Что измеряет |
|---------|-------|-------------|-------------|
| Context Precision | `ContextPrecision` | ✓ reference | Доля релевантных чанков в топе: сигнал ли ранкинг? |
| Context Recall | `ContextRecall` | ✓ reference | Покрыт ли ground truth контекстом? |
| Context Entity Recall | `ContextEntityRecall` | ✓ reference | Покрыты ли сущности из GT в контексте? |
| Noise Sensitivity | `NoiseSensitivity` | ✓ reference | Падает ли качество при шуме в контексте? |

### Generation метрики

| Метрика | Класс | Ground Truth | Что измеряет |
|---------|-------|-------------|-------------|
| Faithfulness | `Faithfulness` | ✗ | Все ли утверждения в ответе подтверждаются контекстом? |
| Answer Relevancy | `AnswerRelevancy` | ✗ | Релевантен ли ответ вопросу? (через embeddings) |
| Answer Correctness | `AnswerCorrectness` | ✓ reference | Фактическая + семантическая корректность vs GT |
| Answer Similarity | `AnswerSimilarity` | ✓ reference | Семантическое сходство с GT |

### Без ground_truth (работают без reference)

Для нашего датасета (если expected_output есть — используем, нет — пропускаем):
- `Faithfulness` — всегда доступна
- `AnswerRelevancy` — всегда доступна (требует embeddings)
- Остальные — только если есть `reference`

## Импорты

```python
from ragas.metrics import (
    Faithfulness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    AnswerCorrectness,
    AnswerSimilarity,
    ContextEntityRecall,
    NoiseSensitivity,
)
```

## Формат результатов

`result.to_pandas()` возвращает DataFrame:

```
user_input | response | retrieved_contexts | reference | faithfulness | answer_relevancy | context_precision | context_recall | answer_correctness
```

Каждая метрика: float от 0.0 до 1.0. `NaN` если метрика не применима.

`result.scores` — список dict:
```python
[
  {"faithfulness": 0.85, "answer_relevancy": 0.92, ...},
  ...
]
```

## Кастомные метрики

### API для создания кастомной метрики

```python
from ragas.metrics.base import MetricWithLLM, SingleTurnMetric
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class MyCustomMetric(MetricWithLLM, SingleTurnMetric):
    """
    Кастомная метрика — описание что она измеряет.
    """
    name: str = "my_custom_metric"

    async def _single_turn_ascore(
        self, sample: SingleTurnSample, callbacks=None
    ) -> float:
        """
        Принимает SingleTurnSample, возвращает float 0.0-1.0.
        """
        # Используем self.llm для вызова LLM-судьи
        prompt = f"Оцени ответ: {sample.response}"
        result = await self.llm.agenerate([prompt])
        score = parse_score(result)
        return score
```

### Минимальный шаблон с промптом

```python
from ragas.prompt import PydanticPrompt
from pydantic import BaseModel

class ScoreOutput(BaseModel):
    score: float
    reason: str

class MyPrompt(PydanticPrompt[dict, ScoreOutput]):
    instruction = "Оцени качество ответа по шкале 0-1."
    input_model = dict
    output_model = ScoreOutput

@dataclass
class MyMetric(MetricWithLLM, SingleTurnMetric):
    name: str = "completeness"
    my_prompt: MyPrompt = field(default_factory=MyPrompt)

    async def _single_turn_ascore(self, sample, callbacks=None):
        out = await self.my_prompt.generate(
            data={"question": sample.user_input, "answer": sample.response},
            llm=self.llm,
        )
        return out.score
```

## Документация по кастомным метрикам (для UI)

Встроенная документация должна объяснять:

1. **Что такое кастомная метрика** — любая логика оценки, реализованная как Python-класс
2. **Где разместить** — создать файл `eval/custom_metrics/my_metric.py`
3. **Как подключить** — добавить в `RAGAS_CUSTOM_METRICS` в `eval_ragas_metrics.py`
4. **Шаблон** — копируемый boilerplate с комментариями на русском

## Table Stakes vs Differentiators

### Table Stakes (должны быть в v1)
- Faithfulness + AnswerRelevancy (core RAGAS метрики)
- ContextPrecision + ContextRecall (retrieval quality)
- AnswerCorrectness (end-to-end quality)

### Differentiators (можно добавить позже)
- Кастомные метрики (domain-specific)
- NoiseSensitivity (robustness testing)
- AnswerSimilarity (semantic closeness)
- Batch comparison между прогонами
