"""
DeepEval тесты для RAG-эндпоинта POST /api/v1/eval/rag

API вызывается ОДИН раз на вопрос — ответ переиспользуется всеми метриками.

Запуск:
  pytest tests/eval/ -v -k "TC-001 or TC-002 or TC-003"
  pytest tests/eval/ -v --dataset eval/datasets/my_dataset.json
  pytest tests/eval/ -v --api-url https://assist.dev.mglk.ru
"""

import pytest
from deepeval import assert_test
from deepeval.metrics import (
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric,
    FaithfulnessMetric,
)
from deepeval.test_case import LLMTestCase

# ── Тест 1: Answer Relevancy ─────────────────────────────────────────────────


def test_answer_relevancy(api_response, judge, case):
    tc = LLMTestCase(
        input=case["question"],
        actual_output=api_response["answer"],
        expected_output=case.get("expected_output"),
        retrieval_context=[c["content"] for c in api_response.get("retrieved_chunks", [])],
    )
    assert_test(tc, [AnswerRelevancyMetric(threshold=0.7, model=judge)])


# ── Тест 2: Faithfulness ─────────────────────────────────────────────────────


def test_faithfulness(api_response, judge, case):
    chunks = [c["content"] for c in api_response.get("retrieved_chunks", [])]
    if not chunks:
        pytest.skip(f"[{case['id']}] API не вернул retrieved_chunks")
    tc = LLMTestCase(
        input=case["question"],
        actual_output=api_response["answer"],
        retrieval_context=chunks,
    )
    assert_test(tc, [FaithfulnessMetric(threshold=0.8, model=judge)])


# ── Тест 3: Contextual Precision ─────────────────────────────────────────────


def test_contextual_precision(api_response, judge, case):
    chunks = [c["content"] for c in api_response.get("retrieved_chunks", [])]
    if not chunks:
        pytest.skip(f"[{case['id']}] Нет retrieved_chunks")
    tc = LLMTestCase(
        input=case["question"],
        actual_output=api_response["answer"],
        expected_output=case["expected_output"],
        retrieval_context=chunks,
    )
    assert_test(tc, [ContextualPrecisionMetric(threshold=0.7, model=judge)])


# ── Тест 4: Contextual Recall ─────────────────────────────────────────────────


def test_contextual_recall(api_response, judge, case):
    chunks = [c["content"] for c in api_response.get("retrieved_chunks", [])]
    if not chunks:
        pytest.skip(f"[{case['id']}] Нет retrieved_chunks")
    tc = LLMTestCase(
        input=case["question"],
        actual_output=api_response["answer"],
        expected_output=case["expected_output"],
        retrieval_context=chunks,
    )
    assert_test(tc, [ContextualRecallMetric(threshold=0.6, model=judge)])


# ── Тест 5: Схема ответа ─────────────────────────────────────────────────────


def test_response_schema(api_response, case):
    assert "answer" in api_response and api_response["answer"], "answer пустой"
    assert "retrieved_chunks" in api_response, "нет retrieved_chunks"
    assert isinstance(api_response["retrieved_chunks"], list)
    if "chunks_count" in api_response:
        assert api_response["chunks_count"] == len(api_response["retrieved_chunks"])


# ── Тест 6: Невалидный category → 422 ────────────────────────────────────────


def test_invalid_category_returns_422(http_client):
    response = http_client.post(
        "/api/v1/eval/rag",
        json={"question": "тест", "category": "unknown_intent"},
    )
    assert response.status_code == 422, f"Ожидали 422, получили {response.status_code}"


# ── Тест 7: Пустой вопрос ────────────────────────────────────────────────────


def test_empty_question(http_client):
    response = http_client.post(
        "/api/v1/eval/rag",
        json={"question": "", "category": "dining"},
    )
    assert response.status_code in (422, 500), f"Ожидали ошибку, получили {response.status_code}"
