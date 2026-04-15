"""Tests for business logic used in src/dashboard/app.py.

Streamlit itself cannot be run headlessly in unit tests, so we test the
pure-Python logic: KPI calculations, OWASP category mapping, comparison
table construction, and the helper that builds the cat_map summary.
"""
import json

import pandas as pd
import pytest

from src.red_team.severity import SEVERITY_ORDER, get_owasp_category
from src.reports.generator import calculate_security_score


# --- Sample DataFrame matching app expectations ---

@pytest.fixture()
def scan_df():
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
            "conversations": json.dumps([{"input": "x", "output": "y", "score": 1, "reason": "r"}]),
        },
        {
            "vulnerability": "PromptLeakageType.INSTRUCTIONS",
            "owasp_id": "LLM07", "owasp_name": "Утечка промпта",
            "severity": "High", "pass_rate": 1.0, "asr": 0.0,
            "passed": 1, "failed": 0, "errored": 0, "total": 1,
            "attack_type": "Roleplay",
            "model_version": "qwen/qwen-2.5-7b-instruct",
            "judge_version": "gpt-4o-mini",
            "session_id": "", "timestamp": "2026-03-31T12:00:00+00:00",
            "conversations": json.dumps([{"input": "leak?", "output": "no", "score": 0, "reason": "safe"}]),
        },
    ])


# --- KPI row calculations (replicated from app.py) ---

def test_kpi_total_tests(scan_df):
    assert int(scan_df["total"].sum()) == 2


def test_kpi_total_failed(scan_df):
    assert int(scan_df["failed"].sum()) == 1


def test_kpi_overall_asr(scan_df):
    total = int(scan_df["total"].sum())
    failed = int(scan_df["failed"].sum())
    asr = failed / total if total > 0 else 0.0
    assert asr == 0.5


def test_kpi_asr_zero_when_no_tests():
    empty = pd.DataFrame(columns=["total", "failed"])
    total = int(empty["total"].sum()) if not empty.empty else 0
    failed = int(empty["failed"].sum()) if not empty.empty else 0
    asr = failed / total if total > 0 else 0.0
    assert asr == 0.0


def test_security_score_from_scan_df(scan_df):
    score = calculate_security_score(scan_df)
    assert 0.0 <= score <= 100.0


# --- cat_map construction (replicated from app.py) ---

def _build_cat_map(df: pd.DataFrame) -> dict:
    cat_map: dict = {}
    for _, row in df.iterrows():
        cat = get_owasp_category(row["vulnerability"])
        key = cat.id
        if key not in cat_map or row["asr"] > cat_map[key]["asr"]:
            cat_map[key] = {
                "id": cat.id, "name": cat.name,
                "severity": cat.severity.value, "asr": row["asr"],
            }
    return cat_map


def test_cat_map_has_two_categories(scan_df):
    cat_map = _build_cat_map(scan_df)
    assert len(cat_map) == 2


def test_cat_map_ids(scan_df):
    cat_map = _build_cat_map(scan_df)
    assert "LLM09" in cat_map
    assert "LLM07" in cat_map


def test_cat_map_worst_asr_wins():
    """When two rows map to the same category, the highest ASR wins."""
    df = pd.DataFrame([
        {"vulnerability": "ToxicityType.INSULTS", "asr": 0.2},
        {"vulnerability": "ToxicityType.HATE", "asr": 0.8},
    ])
    cat_map = _build_cat_map(df)
    assert cat_map["LLM09"]["asr"] == 0.8


def test_cat_map_severity_order(scan_df):
    """All severities in cat_map must be valid SEVERITY_ORDER values."""
    cat_map = _build_cat_map(scan_df)
    for entry in cat_map.values():
        assert entry["severity"] in SEVERITY_ORDER


# --- Comparison table logic (replicated from app.py tab4) ---

def _build_comparison_rows(df_a: pd.DataFrame, df_b: pd.DataFrame) -> list[dict]:
    dfa = df_a.set_index("vulnerability")
    dfb = df_b.set_index("vulnerability")
    all_vulns = sorted(set(dfa.index) | set(dfb.index))
    rows = []
    for v in all_vulns:
        asr_a = float(dfa.loc[v, "asr"]) if v in dfa.index else None
        asr_b = float(dfb.loc[v, "asr"]) if v in dfb.index else None
        if asr_a is not None and asr_b is not None:
            delta = asr_b - asr_a
            if delta < -0.01:
                trend = "улучшилось"
            elif delta > 0.01:
                trend = "ухудшилось"
            else:
                trend = "без изменений"
        elif asr_a is None:
            delta, trend = None, "новый тест"
        else:
            delta, trend = None, "отсутствует в B"
        rows.append({"vuln": v, "asr_a": asr_a, "asr_b": asr_b, "delta": delta, "trend": trend})
    return rows


def test_comparison_improved():
    df_a = pd.DataFrame([{"vulnerability": "ToxicityType.INSULTS", "asr": 0.8}])
    df_b = pd.DataFrame([{"vulnerability": "ToxicityType.INSULTS", "asr": 0.2}])
    rows = _build_comparison_rows(df_a, df_b)
    assert rows[0]["trend"] == "улучшилось"
    assert rows[0]["delta"] == pytest.approx(-0.6)


def test_comparison_worsened():
    df_a = pd.DataFrame([{"vulnerability": "ToxicityType.INSULTS", "asr": 0.1}])
    df_b = pd.DataFrame([{"vulnerability": "ToxicityType.INSULTS", "asr": 0.9}])
    rows = _build_comparison_rows(df_a, df_b)
    assert rows[0]["trend"] == "ухудшилось"


def test_comparison_unchanged():
    df_a = pd.DataFrame([{"vulnerability": "ToxicityType.INSULTS", "asr": 0.5}])
    df_b = pd.DataFrame([{"vulnerability": "ToxicityType.INSULTS", "asr": 0.5}])
    rows = _build_comparison_rows(df_a, df_b)
    assert rows[0]["trend"] == "без изменений"
    assert rows[0]["delta"] == pytest.approx(0.0)


def test_comparison_new_in_b():
    df_a = pd.DataFrame([{"vulnerability": "ToxicityType.INSULTS", "asr": 0.5}])
    df_b = pd.DataFrame([
        {"vulnerability": "ToxicityType.INSULTS", "asr": 0.5},
        {"vulnerability": "BiasType.RACE", "asr": 0.3},
    ])
    rows = _build_comparison_rows(df_a, df_b)
    new_row = next(r for r in rows if r["vuln"] == "BiasType.RACE")
    assert new_row["trend"] == "новый тест"
    assert new_row["asr_a"] is None


def test_comparison_missing_in_b():
    df_a = pd.DataFrame([
        {"vulnerability": "ToxicityType.INSULTS", "asr": 0.5},
        {"vulnerability": "BiasType.RACE", "asr": 0.3},
    ])
    df_b = pd.DataFrame([{"vulnerability": "ToxicityType.INSULTS", "asr": 0.5}])
    rows = _build_comparison_rows(df_a, df_b)
    missing = next(r for r in rows if r["vuln"] == "BiasType.RACE")
    assert missing["trend"] == "отсутствует в B"
    assert missing["asr_b"] is None
