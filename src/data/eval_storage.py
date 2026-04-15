"""Reader for eval/results — RAG quality metrics JSON files."""

import json
import logging
import os
from pathlib import Path

import pandas as pd

EVAL_RESULTS_DIR = Path(os.getenv("EVAL_RESULTS_DIR", "eval/results"))


def list_eval_runs() -> list[dict]:
    """Return metadata list for all eval runs, newest first.

    Each entry: {path, label, df, ar_mean, pass_rate}
    """
    if not EVAL_RESULTS_DIR.exists():
        return []

    result = []
    for run_dir in sorted(EVAL_RESULTS_DIR.iterdir(), reverse=True):
        metrics_file = run_dir / "metrics.json"
        if not metrics_file.exists():
            continue
        try:
            df = load_eval_run(metrics_file)
            if df.empty:
                continue
            ar_mean = float(df["answer_relevancy_score"].dropna().mean()) if "answer_relevancy_score" in df.columns else 0.0
            pass_rate = float(df["answer_relevancy_passed"].mean()) if "answer_relevancy_passed" in df.columns else 0.0
            label = f"{run_dir.name} | AR={ar_mean:.3f} | pass={pass_rate:.0%}"
            result.append({
                "path": metrics_file,
                "label": label,
                "df": df,
                "ar_mean": ar_mean,
                "pass_rate": pass_rate,
            })
        except Exception as e:
            logging.warning(f"[eval_storage] Skipping broken run {run_dir.name}: {e}")
            continue
    return result


def load_eval_run(path: Path) -> pd.DataFrame:
    """Load a single metrics.json file into a DataFrame."""
    with open(path, encoding="utf-8") as f:
        records = json.load(f)
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def load_latest_eval() -> pd.DataFrame | None:
    """Load the most recent eval run."""
    runs = list_eval_runs()
    if not runs:
        return None
    return runs[0]["df"]


def quality_score(df: pd.DataFrame) -> float:
    """Overall quality score 0-100 from answer_relevancy_score.

    Returns 0.0 for empty or missing data.
    """
    if df is None or df.empty:
        return 0.0
    col = "answer_relevancy_score"
    if col not in df.columns:
        return 0.0
    scores = df[col].dropna()
    if scores.empty:
        return 0.0
    return float(scores.mean()) * 100.0
