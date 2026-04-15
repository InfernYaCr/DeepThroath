"""Tests for src/reports/generator.py"""
import json

import pandas as pd
import pytest

from src.reports.generator import (
    build_report_context,
    calculate_security_score,
)


@pytest.fixture()
def sample_df():
    return pd.DataFrame([
        {
            "vulnerability": "ToxicityType.INSULTS",
            "owasp_id": "LLM09", "owasp_name": "Токсичность",
            "severity": "Medium", "pass_rate": 0.0, "asr": 1.0,
            "passed": 0, "failed": 1, "errored": 0, "total": 1,
            "attack_type": "PromptInjection",
            "model_version": "qwen/qwen-2.5-7b-instruct",
            "judge_version": "gpt-4o-mini",
            "session_id": "", "timestamp": "2026-03-31T12:00:00+00:00",
            "conversations": json.dumps([{"input": "attack", "output": "bad", "score": 1, "reason": "toxic"}]),
        },
        {
            "vulnerability": "PromptLeakageType.INSTRUCTIONS",
            "owasp_id": "LLM07", "owasp_name": "Утечка системного промпта",
            "severity": "High", "pass_rate": 1.0, "asr": 0.0,
            "passed": 1, "failed": 0, "errored": 0, "total": 1,
            "attack_type": "Roleplay",
            "model_version": "qwen/qwen-2.5-7b-instruct",
            "judge_version": "gpt-4o-mini",
            "session_id": "", "timestamp": "2026-03-31T12:00:00+00:00",
            "conversations": json.dumps([{"input": "leak?", "output": "no", "score": 0, "reason": "safe"}]),
        },
    ])


# --- calculate_security_score ---

def test_score_empty_df_returns_zero():
    assert calculate_security_score(pd.DataFrame()) == 0.0


def test_score_all_passed():
    df = pd.DataFrame([{
        "severity": "Critical", "pass_rate": 1.0, "asr": 0.0,
        "passed": 1, "failed": 0, "total": 1,
    }])
    assert calculate_security_score(df) == 100.0


def test_score_all_failed():
    df = pd.DataFrame([{
        "severity": "Critical", "pass_rate": 0.0, "asr": 1.0,
        "passed": 0, "failed": 1, "total": 1,
    }])
    assert calculate_security_score(df) == 0.0


def test_score_between_0_and_100(sample_df):
    score = calculate_security_score(sample_df)
    assert 0.0 <= score <= 100.0


def test_score_unknown_severity_uses_low_weight():
    df = pd.DataFrame([{
        "severity": "Unknown", "pass_rate": 1.0, "asr": 0.0,
        "passed": 1, "failed": 0, "total": 1,
    }])
    score = calculate_security_score(df)
    assert score == 100.0


# --- build_report_context ---

def test_report_context_has_required_keys(sample_df):
    ctx = build_report_context(sample_df, pd.DataFrame(), client_name="Test Corp")
    required = [
        "client_name", "generated_at", "model_version", "judge_version",
        "security_score", "total_tests", "total_failed", "overall_asr",
        "top_vulnerabilities", "owasp_results", "recommendations", "methodology",
    ]
    for key in required:
        assert key in ctx, f"Missing key: {key}"


def test_report_context_client_name(sample_df):
    ctx = build_report_context(sample_df, pd.DataFrame(), client_name="Acme Inc")
    assert ctx["client_name"] == "Acme Inc"


def test_report_context_totals(sample_df):
    ctx = build_report_context(sample_df, pd.DataFrame())
    assert ctx["total_tests"] == 2
    assert ctx["total_failed"] == 1


def test_report_context_no_history_score_delta_none(sample_df):
    ctx = build_report_context(sample_df, pd.DataFrame())
    assert ctx["score_delta"] is None


def test_report_context_owasp_results_length(sample_df):
    ctx = build_report_context(sample_df, pd.DataFrame())
    assert len(ctx["owasp_results"]) == 2


def test_report_context_recommendations_only_failed(sample_df):
    ctx = build_report_context(sample_df, pd.DataFrame())
    # Only Toxicity failed → should have recommendation
    assert len(ctx["recommendations"]) >= 1
    owasp_ids = [r["owasp_id"] for r in ctx["recommendations"]]
    assert "LLM09" in owasp_ids


def test_report_context_methodology_has_attacks(sample_df):
    ctx = build_report_context(sample_df, pd.DataFrame())
    attacks = ctx["methodology"]["attacks"]
    assert "PromptInjection" in attacks or "Roleplay" in attacks


def test_report_context_empty_df():
    """Empty df should not crash — returns zeroed context."""
    from src.data.transformer import transform_risk_assessment
    # Use an empty DataFrame with correct columns
    from src.data.storage import load_latest
    empty = pd.DataFrame(columns=[
        "vulnerability", "owasp_id", "owasp_name", "severity",
        "pass_rate", "asr", "passed", "failed", "errored", "total",
        "attack_type", "model_version", "judge_version", "session_id",
        "timestamp", "conversations",
    ])
    ctx = build_report_context(empty, pd.DataFrame())
    assert ctx["security_score"] == 0.0
    assert ctx["total_tests"] == 0
