"""Tests for src/data/eval_storage.py"""

import json
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture()
def eval_results_dir(tmp_path, monkeypatch):
    """Redirect eval_storage module to a temp directory."""
    monkeypatch.setenv("EVAL_RESULTS_DIR", str(tmp_path))
    import src.data.eval_storage as es

    es.EVAL_RESULTS_DIR = tmp_path
    return tmp_path


@pytest.fixture()
def sample_metrics():
    return [
        {
            "session_id": "s1",
            "top_k": 10,
            "category": "greetings",
            "intent": "general",
            "user_query": "What is AI?",
            "expected_answer": "Artificial Intelligence",
            "actual_answer": "AI is a branch of computer science.",
            "answer_relevancy_score": 0.85,
            "answer_relevancy_passed": True,
            "answer_relevancy_reason": "The answer is relevant.",
            "faithfulness_score": 0.9,
            "faithfulness_passed": True,
            "faithfulness_reason": "Faithful to context.",
        },
        {
            "session_id": "s2",
            "top_k": 10,
            "category": "greetings",
            "intent": "general",
            "user_query": "How are you?",
            "expected_answer": "I am fine.",
            "actual_answer": "I am doing well.",
            "answer_relevancy_score": 0.6,
            "answer_relevancy_passed": False,
            "answer_relevancy_reason": "Partially relevant.",
            "faithfulness_score": None,
            "faithfulness_passed": None,
            "faithfulness_reason": "no retrieval_context",
        },
    ]


def _write_run(base_dir: Path, run_name: str, metrics: list) -> Path:
    run_dir = base_dir / run_name
    run_dir.mkdir(parents=True, exist_ok=True)
    metrics_file = run_dir / "metrics.json"
    metrics_file.write_text(json.dumps(metrics, ensure_ascii=False), encoding="utf-8")
    return metrics_file


# --- list_eval_runs ---


def test_list_eval_runs_empty_when_no_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("EVAL_RESULTS_DIR", str(tmp_path / "nonexistent"))
    import src.data.eval_storage as es

    es.EVAL_RESULTS_DIR = tmp_path / "nonexistent"
    result = es.list_eval_runs()
    assert result == []


def test_list_eval_runs_returns_entries(eval_results_dir, sample_metrics):
    from src.data.eval_storage import list_eval_runs

    _write_run(eval_results_dir, "20260101_120000_test", sample_metrics)
    runs = list_eval_runs()
    assert len(runs) == 1
    entry = runs[0]
    assert "path" in entry
    assert "label" in entry
    assert "df" in entry
    assert "ar_mean" in entry
    assert "pass_rate" in entry


def test_list_eval_runs_newest_first(eval_results_dir, sample_metrics):
    from src.data.eval_storage import list_eval_runs

    _write_run(eval_results_dir, "20260101_120000_first", sample_metrics)
    _write_run(eval_results_dir, "20260102_120000_second", sample_metrics)
    runs = list_eval_runs()
    assert len(runs) == 2
    # Newest first (reverse sort)
    assert "second" in runs[0]["label"] or runs[0]["path"].parent.name > runs[1]["path"].parent.name


# --- load_eval_run ---


def test_load_eval_run_returns_dataframe(eval_results_dir, sample_metrics):
    from src.data.eval_storage import load_eval_run

    metrics_file = _write_run(eval_results_dir, "run1", sample_metrics)
    df = load_eval_run(metrics_file)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "answer_relevancy_score" in df.columns


def test_load_eval_run_empty_json(eval_results_dir):
    from src.data.eval_storage import load_eval_run

    run_dir = eval_results_dir / "empty_run"
    run_dir.mkdir()
    metrics_file = run_dir / "metrics.json"
    metrics_file.write_text("[]", encoding="utf-8")
    df = load_eval_run(metrics_file)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


# --- quality_score ---


def test_quality_score_empty_returns_zero():
    from src.data.eval_storage import quality_score

    assert quality_score(pd.DataFrame()) == 0.0


def test_quality_score_none_returns_zero():
    from src.data.eval_storage import quality_score

    assert quality_score(None) == 0.0


def test_quality_score_calculation(sample_metrics):
    from src.data.eval_storage import quality_score

    df = pd.DataFrame(sample_metrics)
    score = quality_score(df)
    # (0.85 + 0.6) / 2 * 100 = 72.5
    assert abs(score - 72.5) < 0.01


def test_quality_score_all_passed():
    from src.data.eval_storage import quality_score

    df = pd.DataFrame(
        [
            {"answer_relevancy_score": 0.9},
            {"answer_relevancy_score": 0.8},
            {"answer_relevancy_score": 1.0},
        ]
    )
    score = quality_score(df)
    assert abs(score - 90.0) < 0.01


def test_quality_score_missing_column():
    from src.data.eval_storage import quality_score

    df = pd.DataFrame([{"session_id": "s1", "category": "test"}])
    assert quality_score(df) == 0.0
