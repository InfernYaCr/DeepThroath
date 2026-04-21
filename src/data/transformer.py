import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.red_team.severity import get_owasp_category


def transform_risk_assessment(
    risk_assessment: Any,
    model_version: str,
    judge_version: str = "N/A",
    session_id: str | None = None,
) -> pd.DataFrame:
    """Convert a DeepTeam RiskAssessment to an analytics-ready DataFrame."""
    timestamp = datetime.now(timezone.utc).isoformat()
    records = []

    vuln_results = risk_assessment.overview.vulnerability_type_results
    test_cases = list(risk_assessment.test_cases)

    for vr in vuln_results:
        vuln_name = str(vr.vulnerability_type or vr.vulnerability or "Unknown")
        owasp = get_owasp_category(vuln_name)

        passed = int(vr.passing or 0)
        failed = int(vr.failing or 0)
        errored = int(vr.errored or 0)
        total = passed + failed
        pass_rate = float(vr.pass_rate) if vr.pass_rate is not None else (passed / total if total > 0 else 0.0)

        # Collect conversations for this vulnerability
        convs = []
        for tc in test_cases:
            tc_vuln = str(tc.vulnerability_type or tc.vulnerability or "")
            if tc_vuln != vuln_name:
                continue
            convs.append(
                {
                    "input": tc.input or "",
                    "output": tc.actual_output or "",
                    "score": tc.score,
                    "reason": tc.reason or "",
                    "attack_method": str(tc.attack_method or ""),
                    "error": tc.error or None,
                }
            )

        attack_types = list({c["attack_method"] for c in convs if c["attack_method"]})

        records.append(
            {
                "vulnerability": vuln_name,
                "owasp_id": owasp.id,
                "owasp_name": owasp.name,
                "severity": owasp.severity.value,
                "pass_rate": round(pass_rate, 4),
                "asr": round(1.0 - pass_rate, 4),
                "passed": passed,
                "failed": failed,
                "errored": errored,
                "total": total,
                "attack_type": ", ".join(attack_types) if attack_types else "Unknown",
                "model_version": model_version,
                "judge_version": judge_version,
                "session_id": session_id or "",
                "timestamp": timestamp,
                "conversations": json.dumps(convs, ensure_ascii=False),
            }
        )

    if not records:
        return pd.DataFrame(
            columns=[
                "vulnerability",
                "owasp_id",
                "owasp_name",
                "severity",
                "pass_rate",
                "asr",
                "passed",
                "failed",
                "errored",
                "total",
                "attack_type",
                "model_version",
                "judge_version",
                "session_id",
                "timestamp",
                "conversations",
            ]
        )
    return pd.DataFrame(records)
