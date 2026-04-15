"""Tests for src/data/storage.py"""
import os
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture()
def results_dir(tmp_path, monkeypatch):
    """Redirect storage module to a temp directory."""
    monkeypatch.setenv("RESULTS_DIR", str(tmp_path))
    # Re-import with patched env so module-level paths are recalculated
    import importlib
    import src.data.storage as storage
    storage.RESULTS_DIR = tmp_path
    storage.LATEST_FILE = tmp_path / "latest.parquet"
    storage.HISTORY_DIR = tmp_path / "history"
    return tmp_path


@pytest.fixture()
def sample_df():
    return pd.DataFrame([{
        "vulnerability": "PromptLeakageType.INSTRUCTIONS",
        "owasp_id": "LLM07",
        "owasp_name": "Утечка системного промпта",
        "severity": "High",
        "pass_rate": 1.0,
        "asr": 0.0,
        "passed": 1,
        "failed": 0,
        "errored": 0,
        "total": 1,
        "attack_type": "PromptInjection",
        "model_version": "qwen/qwen-2.5-7b-instruct",
        "judge_version": "gpt-4o-mini",
        "session_id": "",
        "timestamp": "2026-03-31T12:00:00+00:00",
        "conversations": "[]",
    }])


# --- save_results ---

def test_save_results_creates_latest(results_dir, sample_df):
    from src.data.storage import save_results
    path = save_results(sample_df)
    assert path.exists()
    assert path.name == "latest.parquet"


def test_save_results_creates_history_file(results_dir, sample_df):
    from src.data.storage import save_results
    save_results(sample_df)
    history_files = list((results_dir / "history").glob("*.parquet"))
    assert len(history_files) == 1


def test_save_results_roundtrip(results_dir, sample_df):
    from src.data.storage import save_results, load_latest
    save_results(sample_df)
    loaded = load_latest()
    assert loaded is not None
    assert list(loaded.columns) == list(sample_df.columns)
    assert len(loaded) == 1


# --- load_latest ---

def test_load_latest_returns_none_when_missing(results_dir):
    from src.data.storage import load_latest
    assert load_latest() is None


def test_load_latest_returns_dataframe(results_dir, sample_df):
    from src.data.storage import save_results, load_latest
    save_results(sample_df)
    result = load_latest()
    assert isinstance(result, pd.DataFrame)
    assert not result.empty


# --- load_history ---

def test_load_history_empty_when_no_dir(results_dir):
    from src.data.storage import load_history
    result = load_history()
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_load_history_concatenates_multiple_scans(results_dir, sample_df):
    from src.data.storage import save_results, load_history
    save_results(sample_df)
    save_results(sample_df)
    history = load_history()
    assert len(history) == 2


def test_load_history_skips_broken_file(results_dir, sample_df, caplog):
    import logging
    from src.data.storage import save_results, load_history
    save_results(sample_df)
    # Write a broken parquet file
    broken = results_dir / "history" / "broken.parquet"
    broken.write_bytes(b"this is not parquet")
    with caplog.at_level(logging.WARNING):
        history = load_history()
    assert len(history) == 1
    assert "broken.parquet" in caplog.text


def test_load_history_skips_empty_dataframes(results_dir, sample_df):
    from src.data.storage import save_results, load_history
    save_results(sample_df)
    # Save an empty df directly as parquet
    empty = results_dir / "history" / "empty.parquet"
    pd.DataFrame().to_parquet(empty)
    history = load_history()
    assert len(history) == 1


# --- list_scan_files ---

def test_list_scan_files_empty_when_no_history(results_dir):
    from src.data.storage import list_scan_files
    assert list_scan_files() == []


def test_list_scan_files_returns_metadata(results_dir, sample_df):
    from src.data.storage import save_results, list_scan_files
    save_results(sample_df)
    files = list_scan_files()
    assert len(files) == 1
    entry = files[0]
    assert "label" in entry
    assert "df" in entry
    assert "path" in entry
    assert "qwen/qwen-2.5-7b-instruct" in entry["label"]


def test_list_scan_files_skips_broken(results_dir, sample_df, caplog):
    import logging
    from src.data.storage import save_results, list_scan_files
    save_results(sample_df)
    broken = results_dir / "history" / "zzz_broken.parquet"
    broken.write_bytes(b"garbage")
    with caplog.at_level(logging.WARNING):
        files = list_scan_files()
    assert len(files) == 1
    assert "zzz_broken.parquet" in caplog.text
