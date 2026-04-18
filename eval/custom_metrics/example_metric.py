"""
Пример кастомной метрики RAGAS: ExampleCustomMetric (Completeness / Полнота ответа).

Как создать свою метрику
------------------------
1. Скопируй этот файл в eval/custom_metrics/my_metric.py (имя файла произвольно).
2. Переименуй класс (имя класса не важно для автодискавери — важны базовые классы).
3. Замени name = "completeness" на уникальное имя твоей метрики.
4. Замени логику внутри _single_turn_ascore — возвращай float от 0.0 до 1.0.
5. При необходимости изменй CompletenessPrompt и CompletenessOutput под свою задачу.

Как работает автодискавери
--------------------------
Пайплайн eval/eval_ragas_metrics.py сканирует все *.py файлы в
eval/custom_metrics/ через pkgutil.iter_modules, затем проверяет каждый класс:
    issubclass(cls, MetricWithLLM) and issubclass(cls, SingleTurnMetric)
Если оба условия выполнены — класс добавляется в список метрик.

Требования к реализации
-----------------------
- Класс ДОЛЖЕН наследовать MetricWithLLM + SingleTurnMetric (порядок важен).
- Метод _single_turn_ascore ДОЛЖЕН возвращать float в диапазоне 0.0–1.0.
- self.llm инжектируется пайплайном автоматически — не трогать вручную.
- Декоратор @dataclass обязателен (MetricWithLLM использует поля dataclass).

Изменения от оригинала (RAGAS 0.4.3 compatibility)
---------------------------------------------------
- input_model = dict → CompletenessInput(BaseModel)
  В RAGAS 0.4.x PydanticPrompt требует Pydantic-модель с .model_dump_json(),
  plain dict не поддерживается и вызывает AttributeError.
- generate(data={...}) → generate(data=CompletenessInput(...))
"""

from dataclasses import dataclass, field

from pydantic import BaseModel
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics.base import MetricWithLLM, SingleTurnMetric
from ragas.prompt import PydanticPrompt


class CompletenessInput(BaseModel):
    """Входные данные для промпта оценки полноты."""

    question: str
    answer: str


class CompletenessOutput(BaseModel):
    """Структура ответа LLM-судьи: оценка полноты + объяснение."""

    score: float  # 0.0-1.0
    reason: str   # объяснение на русском


class CompletenessPrompt(PydanticPrompt[CompletenessInput, CompletenessOutput]):
    """Промпт для оценки полноты ответа ассистента."""

    instruction = (
        "Ты оцениваешь полноту ответа ассистента относительно вопроса пользователя. "
        "Верни score от 0.0 (ответ неполный/пустой) до 1.0 (ответ полностью покрывает вопрос). "
        "В поле reason напиши объяснение на русском языке."
    )
    input_model = CompletenessInput
    output_model = CompletenessOutput


@dataclass
class ExampleCustomMetric(MetricWithLLM, SingleTurnMetric):
    """Пример кастомной метрики: Completeness (полнота ответа).

    Диапазон: 0.0-1.0. Требует только user_input и response
    (retrieved_contexts и reference не обязательны).

    Подмени name и логику _single_turn_ascore под свою задачу,
    не меняя базовые классы — иначе автодискавери не найдёт тебя.
    """

    name: str = "completeness"
    completeness_prompt: CompletenessPrompt = field(default_factory=CompletenessPrompt)

    async def _single_turn_ascore(
        self, sample: SingleTurnSample, callbacks=None
    ) -> float:
        out = await self.completeness_prompt.generate(
            data=CompletenessInput(
                question=sample.user_input or "",
                answer=sample.response or "",
            ),
            llm=self.llm,
        )
        # Защита от LLM-галлюцинаций: clamp в диапазон 0.0-1.0
        return max(0.0, min(1.0, float(out.score)))
