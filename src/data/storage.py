import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RESULTS_DIR = Path(os.getenv("RESULTS_DIR", "results"))
LATEST_FILE = RESULTS_DIR / "latest.parquet"
HISTORY_DIR = RESULTS_DIR / "history"


def save_results(df: pd.DataFrame) -> Path:
    """Persist results as Parquet and archive a timestamped copy."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    df.to_parquet(LATEST_FILE, index=False)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    df.to_parquet(HISTORY_DIR / f"{ts}.parquet", index=False)

    return LATEST_FILE


def load_latest() -> pd.DataFrame | None:
    """Load the most recent scan results, or None if unavailable."""
    if not LATEST_FILE.exists():
        return None
    return pd.read_parquet(LATEST_FILE)


def load_history() -> pd.DataFrame:
    """Load all historical scans concatenated and sorted by timestamp."""
    if not HISTORY_DIR.exists():
        return pd.DataFrame()

    files = sorted(HISTORY_DIR.glob("*.parquet"))
    if not files:
        return pd.DataFrame()

    frames = []
    for f in files:
        try:
            df = pd.read_parquet(f)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            import logging
            logging.warning(f"[storage] Skipping broken history file {f.name}: {e}")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def list_scan_files() -> list[dict]:
    """Return metadata list for all historical scans, newest first.

    Each entry: {path, label, timestamp_str, model, score_hint}
    """
    if not HISTORY_DIR.exists():
        return []

    result = []
    for f in sorted(HISTORY_DIR.glob("*.parquet"), reverse=True):
        try:
            df = pd.read_parquet(f)
            ts = df["timestamp"].iloc[0][:16].replace("T", " ") if "timestamp" in df.columns else f.stem
            model = df["model_version"].iloc[0] if "model_version" in df.columns else "unknown"
            judge = df["judge_version"].iloc[0] if "judge_version" in df.columns else "N/A"
            total = int(df["total"].sum())
            failed = int(df["failed"].sum())
            label = f"{ts} | {model} | {failed}/{total} провалено"
            result.append({"path": f, "label": label, "df": df})
        except Exception as e:
            import logging
            logging.warning(f"[storage] Skipping broken scan file {f.name}: {e}")
            continue
    return result


def load_scan_file(path: Path) -> pd.DataFrame:
    """Load a specific historical scan by path."""
    return pd.read_parquet(path)
