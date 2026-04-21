import json
from unittest.mock import MagicMock

from src.data.transformer import transform_risk_assessment


def _make_risk(rows: list[dict]) -> MagicMock:
    mock = MagicMock()
    mock.overview.vulnerability_type_results = []
    mock.test_cases = []
    for r in rows:
        vtr = MagicMock()
        vtr.vulnerability = r.get("vulnerability")
        vtr.vulnerability_type = r.get("vulnerability")
        vtr.pass_rate = None
        vtr.passing = r.get("passed", 0)
        vtr.failing = r.get("failed", 0)
        vtr.errored = 0
        mock.overview.vulnerability_type_results.append(vtr)

        tc_count = r.get("conversations") or [
            {"input": "dummy", "output": "dummy", "score": 0, "attack_type": r.get("attack_type", "")}
        ]
        for c in tc_count:
            tc = MagicMock()
            tc.vulnerability = r.get("vulnerability")
            tc.vulnerability_type = r.get("vulnerability")
            tc.input = c.get("input", "")
            tc.actual_output = c.get("output", "")
            tc.score = c.get("score", 0)
            tc.reason = ""
            tc.attack_method = c.get("attack_type", r.get("attack_type", ""))
            tc.error = None
            mock.test_cases.append(tc)

    return mock


def test_adds_owasp_fields_for_known_vulnerability():
    risk = _make_risk(
        [
            {
                "vulnerability": "PromptInjection",
                "passed": 20,
                "failed": 5,
                "attack_type": "PromptInjectionAttack",
                "conversations": [],
            }
        ]
    )
    df = transform_risk_assessment(risk, model_version="v1")
    assert df.iloc[0]["owasp_id"] == "LLM01"
    assert df.iloc[0]["severity"] == "Critical"


def test_calculates_asr_and_pass_rate():
    risk = _make_risk(
        [
            {
                "vulnerability": "DataLeakage",
                "passed": 20,
                "failed": 5,
                "attack_type": "SingleTurnAttack",
                "conversations": [],
            }
        ]
    )
    df = transform_risk_assessment(risk, model_version="v1")
    assert abs(df.iloc[0]["asr"] - 0.2) < 0.001
    assert abs(df.iloc[0]["pass_rate"] - 0.8) < 0.001


def test_serializes_conversations_to_json_string():
    convs = [{"input": "attack", "output": "bad", "score": 1}]
    risk = _make_risk(
        [
            {
                "vulnerability": "Toxicity",
                "passed": 10,
                "failed": 2,
                "attack_type": "JailbreakingAttack",
                "conversations": convs,
            }
        ]
    )
    df = transform_risk_assessment(risk, model_version="v1")
    stored = json.loads(df.iloc[0]["conversations"])
    assert stored[0]["input"] == "attack"


def test_handles_zero_total_gracefully():
    risk = _make_risk(
        [
            {
                "vulnerability": "Bias",
                "passed": 0,
                "failed": 0,
                "attack_type": "SomeTurn",
                "conversations": [],
            }
        ]
    )
    df = transform_risk_assessment(risk, model_version="v1")
    assert df.iloc[0]["pass_rate"] == 0.0
    assert df.iloc[0]["asr"] == 1.0


def test_unknown_vulnerability_defaults_to_medium():
    risk = _make_risk(
        [
            {
                "vulnerability": "SomeNewThreat",
                "passed": 15,
                "failed": 5,
                "attack_type": "CustomAttack",
                "conversations": [],
            }
        ]
    )
    df = transform_risk_assessment(risk, model_version="v1")
    assert df.iloc[0]["severity"] == "Medium"
    assert df.iloc[0]["owasp_id"] == "LLM09"
