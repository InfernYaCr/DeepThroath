import pandas as pd
import pytest

from src.dashboard.charts import (
    asr_by_owasp_bar,
    overall_passrate_pie,
    passrate_trend,
    severity_heatmap,
)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "vulnerability": "PromptInjection",
            "owasp_id": "LLM01",
            "owasp_name": "Prompt Injection",
            "severity": "Critical",
            "pass_rate": 0.72,
            "asr": 0.28,
            "passed": 18,
            "failed": 7,
            "total": 25,
            "attack_type": "PromptInjectionAttack",
            "model_version": "v1",
            "timestamp": "2026-03-27T00:00:00Z",
        },
        {
            "vulnerability": "DataLeakage",
            "owasp_id": "LLM07",
            "owasp_name": "System Prompt Leakage",
            "severity": "High",
            "pass_rate": 0.88,
            "asr": 0.12,
            "passed": 22,
            "failed": 3,
            "total": 25,
            "attack_type": "CrescendoAttack",
            "model_version": "v1",
            "timestamp": "2026-03-27T00:00:00Z",
        },
    ])


def test_overall_passrate_pie_title(sample_df):
    fig = overall_passrate_pie(sample_df)
    assert "Pass Rate" in fig.layout.title.text


def test_asr_by_owasp_bar_not_empty(sample_df):
    fig = asr_by_owasp_bar(sample_df)
    assert len(fig.data) > 0


def test_passrate_trend_empty_df():
    fig = passrate_trend(pd.DataFrame())
    assert fig is not None


def test_passrate_trend_with_data(sample_df):
    fig = passrate_trend(sample_df)
    assert fig is not None


def test_severity_heatmap_not_empty(sample_df):
    fig = severity_heatmap(sample_df)
    assert fig is not None
