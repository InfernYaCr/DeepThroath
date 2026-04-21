"""
Кастомная метрика: ResortToneMetric — Соответствие тону курорта.

Оценивает, насколько ответ ассистента соответствует стилю премиального курорта:
- Вежливость и гостеприимство (не сухо, не грубо)
- Профессиональный, но тёплый тон
- Отсутствие канцеляризмов и казённых формулировок
- Соответствие ожиданиям гостя 5* отеля

Диапазон: 0.0 (совсем не соответствует тону) — 1.0 (идеально).
Требует только user_input и response (контекст не нужен).
"""

import re
from dataclasses import dataclass, field

from pydantic import BaseModel
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics.base import MetricWithLLM, SingleTurnMetric
from ragas.prompt import PydanticPrompt


class ToneInput(BaseModel):
    question: str
    answer: str


class ToneOutput(BaseModel):
    score: float  # 0.0–1.0
    reason: str  # объяснение на русском


class ResortTonePrompt(PydanticPrompt[ToneInput, ToneOutput]):
    """Промпт для оценки соответствия тону премиального курорта.

    Few-shot примеры помогают моделям с reasoning (Qwen3, DeepSeek-R1) возвращать
    чистый JSON без обёртки в кавычки.
    """

    instruction = (
        "Ты оцениваешь, насколько ответ ассистента соответствует стилю общения "
        "премиального курорта уровня 5 звёзд (Манжерок, Алтай).\n\n"
        "Критерии оценки:\n"
        "  1. Вежливость и гостеприимство — ответ тёплый, заботливый, не сухой.\n"
        "  2. Профессионализм — нет ошибок, нет жаргона, нет грубости.\n"
        "  3. Отсутствие казённости — нет бюрократических формулировок вроде "
        "     «в соответствии с», «согласно регламенту», «уведомляем вас».\n"
        "  4. Ориентация на гостя — ответ решает вопрос гостя, не уходит в сторону.\n"
        "  5. Умеренная эмоциональность — не слишком официально, но и не фамильярно.\n\n"
        "Верни score от 0.0 до 1.0:\n"
        "  0.0–0.3 — тон совсем не подходит (грубо, казённо, безразлично)\n"
        "  0.4–0.6 — приемлемо, но есть заметные недостатки\n"
        "  0.7–0.9 — хороший тон с незначительными замечаниями\n"
        "  1.0     — идеальный тон премиального курорта\n\n"
        "В поле reason напиши краткое объяснение на русском (1–2 предложения)."
    )
    input_model = ToneInput
    output_model = ToneOutput
    # Plain class attribute — PydanticPrompt is a Pydantic model; field() creates
    # a Field descriptor here instead of an actual list, which breaks iteration.
    examples = [
        (
            ToneInput(
                question="Есть ли в отеле бассейн?",
                answer="Да. Бассейн работает с 8:00 до 22:00.",
            ),
            ToneOutput(
                score=0.5,
                reason=(
                    "Ответ технически верен, но слишком лаконичен и сух для общения с гостем 5-звёздочного курорта."
                ),
            ),
        ),
        (
            ToneInput(
                question="Во сколько завтрак?",
                answer=(
                    "Доброе утро! Завтрак в ресторане «Алтай» сервируется "
                    "с 7:30 до 10:30. Будем рады видеть вас — приятного аппетита!"
                ),
            ),
            ToneOutput(
                score=0.95,
                reason=(
                    "Тёплое приветствие, чёткая информация и пожелание приятного "
                    "аппетита создают именно ту атмосферу заботы, которую ожидает "
                    "гость премиального курорта."
                ),
            ),
        ),
    ]


def _extract_score_from_error(err_text: str) -> float | None:
    """Вытаскивает числовой score из текста ошибки PydanticPrompt.

    Reasoning-модели (Qwen3, DeepSeek-R1) иногда возвращают голое число
    вместо JSON-объекта. RAGAS перехватывает это и пишет в ошибку:
      "Input should be an object [... input_value=0.75 ..."
    Мы достаём 0.75 из этой строки — модель правильно посчитала оценку,
    просто неверно отформатировала ответ.
    """
    # Паттерн 1: input_value=<float>
    m = re.search(r"input_value=(-?\d+(?:\.\d+)?)", err_text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    # Паттерн 2: "score":\s*<float> внутри completion content
    m = re.search(r'"score"\s*:\s*(-?\d+(?:\.\d+)?)', err_text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    # Паттерн 3: content='<float>' — модель вернула только число
    m = re.search(r"content='(-?\d+(?:\.\d+)?)'", err_text)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


@dataclass
class ResortToneMetric(MetricWithLLM, SingleTurnMetric):
    """Метрика: соответствие тону премиального курорта.

    Проверяет стиль ответа ассистента без привязки к контексту KB.
    Полезна для выявления ответов, которые технически верны, но звучат
    казённо, холодно или неуместно для гостей 5* отеля.

    Если PydanticPrompt не смог распарсить ответ модели (reasoning-модели
    типа Qwen3 часто возвращают голое число), fallback извлекает score
    напрямую из текста исключения через _extract_score_from_error().
    """

    name: str = "resort_tone"
    tone_prompt: ResortTonePrompt = field(default_factory=ResortTonePrompt)

    async def _single_turn_ascore(self, sample: SingleTurnSample, callbacks=None) -> float:
        tone_input = ToneInput(
            question=sample.user_input or "",
            answer=sample.response or "",
        )
        try:
            out = await self.tone_prompt.generate(
                data=tone_input,
                llm=self.llm,
            )
            return max(0.0, min(1.0, float(out.score)))
        except Exception as primary_err:
            # Fallback: модель посчитала правильно, но вернула голое число или
            # кривой JSON. Извлекаем score из текста ошибки PydanticPrompt.
            score = _extract_score_from_error(str(primary_err))
            if score is not None:
                return max(0.0, min(1.0, score))
            raise primary_err
