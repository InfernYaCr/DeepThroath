import json
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from src.red_team.severity import OWASP_REGISTRY, SEVERITY_WEIGHTS, Severity, get_owasp_category

_REMEDIATION_MAP = {cat.id: cat.remediation for cat in OWASP_REGISTRY.values()}

ReportContext = dict[str, Any]


def calculate_security_score(df: pd.DataFrame) -> float:
    """Weighted pass_rate across severity levels → score 0–100."""
    if df.empty:
        return 0.0
    total_weight = 0.0
    weighted_pass = 0.0
    for _, row in df.iterrows():
        w = SEVERITY_WEIGHTS.get(row["severity"], 0.10)
        weighted_pass += row["pass_rate"] * w
        total_weight += w
    return round((weighted_pass / total_weight) * 100, 1) if total_weight else 0.0


def _top_vulnerabilities(df: pd.DataFrame, n: int = 3) -> list[dict]:
    df2 = df.copy()
    df2["_severity_resolved"] = df2["vulnerability"].map(
        lambda v: get_owasp_category(v).severity.value
    )
    top = (
        df2[df2["_severity_resolved"].isin([Severity.CRITICAL, Severity.HIGH])]
        .sort_values("asr", ascending=False)
        .head(n)
    )
    return [
        {
            "vulnerability": get_owasp_category(r["vulnerability"]).name,
            "owasp_id": get_owasp_category(r["vulnerability"]).id,
            "severity": get_owasp_category(r["vulnerability"]).severity.value,
            "asr": r["asr"],
            "failed": r["failed"],
            "total": r["total"],
        }
        for r in top[["vulnerability", "asr", "failed", "total"]].to_dict("records")
    ]


def _evidence_dialogs(df: pd.DataFrame) -> list[dict]:
    """One representative failed dialog per Critical/High vulnerability."""
    evidence = []
    for _, row in df[df["asr"] > 0].iterrows():
        if row["severity"] not in (Severity.CRITICAL.value, Severity.HIGH.value):
            continue
        convs = row.get("conversations", "[]")
        if isinstance(convs, str):
            try:
                convs = json.loads(convs)
            except json.JSONDecodeError:
                convs = []
        failed = [c for c in convs if c.get("score") == 1]
        if failed:
            evidence.append({
                "vulnerability": row["vulnerability"],
                "owasp_id": row["owasp_id"],
                "severity": row["severity"],
                "attack_type": row["attack_type"],
                "dialog": failed[0],
            })
    return evidence


def _recommendations(df: pd.DataFrame) -> list[dict]:
    seen: set[str] = set()
    recs = []
    for _, row in df[df["asr"] > 0].sort_values("severity").iterrows():
        owasp_id = row["owasp_id"]
        if owasp_id in seen:
            continue
        seen.add(owasp_id)
        recs.append({
            "owasp_id": owasp_id,
            "severity": row["severity"],
            "vulnerability": row["vulnerability"],
            "remediation": _REMEDIATION_MAP.get(owasp_id, "Review OWASP LLM Top 10 guidelines."),
        })
    return recs


def _score_delta(df: pd.DataFrame, history_df: pd.DataFrame) -> float | None:
    if history_df.empty or df.empty:
        return None
    prev = history_df[history_df["timestamp"] < df["timestamp"].min()]
    if prev.empty:
        return None
    return round(calculate_security_score(df) - calculate_security_score(prev), 1)


def build_report_context(
    df: pd.DataFrame,
    history_df: pd.DataFrame,
    client_name: str = "Client",
) -> ReportContext:
    score = calculate_security_score(df)
    return {
        "client_name": client_name,
        "generated_at": datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC"),
        "model_version": df["model_version"].iloc[0] if not df.empty else "N/A",
        "judge_version": df["judge_version"].iloc[0] if ("judge_version" in df.columns and not df.empty) else "N/A",
        "security_score": score,
        "score_delta": _score_delta(df, history_df),
        "total_tests": int(df["total"].sum()),
        "total_failed": int(df["failed"].sum()),
        "overall_asr": round(float(df["asr"].mean()), 4) if not df.empty else 0.0,
        "top_vulnerabilities": _top_vulnerabilities(df),
        "owasp_results": [
            {
                **row,
                # Re-resolve from registry to fix stale/raw names in saved data
                "owasp_id": get_owasp_category(row["vulnerability"]).id,
                "owasp_name": get_owasp_category(row["vulnerability"]).name,
                "severity": get_owasp_category(row["vulnerability"]).severity.value,
            }
            for row in df[
                ["owasp_id", "owasp_name", "severity", "vulnerability", "pass_rate", "asr", "total", "attack_type"]
            ].to_dict("records")
        ],
        "evidence_dialogs": _evidence_dialogs(df),
        "recommendations": _recommendations(df),
        "methodology": {
            "attacks": sorted(df["attack_type"].unique().tolist()) if not df.empty else [],
            "vulnerabilities": sorted([get_owasp_category(v).name for v in df["vulnerability"].unique()]) if not df.empty else [],
            "simulations": int(df["total"].max()) if not df.empty else 0,
        },
    }
