"""Tests for scripts/run_redteam.py — CLI arg parsing, YAML validation, exit codes."""
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_redteam import _find_target, _load_yaml, _validate_attack_config


# --- _load_yaml ---

def test_load_yaml_valid(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("key: value\n")
    result = _load_yaml(str(f))
    assert result == {"key": "value"}


def test_load_yaml_invalid_type(tmp_path):
    f = tmp_path / "config.yaml"
    f.write_text("- just\n- a\n- list\n")
    with pytest.raises(ValueError, match="must be a mapping"):
        _load_yaml(str(f))


# --- _find_target ---

def test_find_target_found(tmp_path):
    f = tmp_path / "targets.yaml"
    f.write_text(yaml.dump({"targets": [
        {"name": "default", "model": "m1", "provider": "anthropic", "system_prompt": "hi"},
        {"name": "strict",  "model": "m2", "provider": "anthropic", "system_prompt": "strict"},
    ]}))
    result = _find_target(str(f), "strict")
    assert result["model"] == "m2"


def test_find_target_not_found_shows_available(tmp_path):
    f = tmp_path / "targets.yaml"
    f.write_text(yaml.dump({"targets": [
        {"name": "default", "model": "m1", "provider": "openrouter", "system_prompt": "hi"},
        {"name": "qwen-7b", "model": "m2", "provider": "openrouter", "system_prompt": "hi"},
    ]}))
    with pytest.raises(ValueError) as exc_info:
        _find_target(str(f), "nonexistent")
    assert "default" in str(exc_info.value)
    assert "qwen-7b" in str(exc_info.value)


# --- _validate_attack_config ---

def test_validate_attack_config_valid():
    cfg = {
        "attacks_per_vulnerability_type": 1,
        "judge_preset": "gemini-flash",
        "attacks": [
            {"name": "PromptInjection", "class": "deepteam.attacks.single_turn.PromptInjection", "enabled": True}
        ],
        "vulnerabilities": [
            {"name": "Toxicity", "class": "deepteam.vulnerabilities.Toxicity", "enabled": True}
        ],
    }
    _validate_attack_config(cfg, "config/test.yaml")  # should not raise


def test_validate_attack_config_missing_class():
    cfg = {
        "attacks": [{"name": "PromptInjection"}],
        "vulnerabilities": [],
    }
    with pytest.raises(ValueError, match="missing 'class'"):
        _validate_attack_config(cfg, "config/test.yaml")


def test_validate_vulnerability_missing_class():
    cfg = {
        "attacks": [],
        "vulnerabilities": [{"name": "Toxicity"}],
    }
    with pytest.raises(ValueError, match="missing 'class'"):
        _validate_attack_config(cfg, "config/test.yaml")


def test_validate_attack_config_empty_sections():
    cfg = {"attacks_per_vulnerability_type": 2, "attacks": [], "vulnerabilities": []}
    _validate_attack_config(cfg, "config/test.yaml")  # should not raise


# --- Exit code integration (mocked) ---

def test_main_exits_1_on_empty_df(tmp_path, monkeypatch):
    """When transformer returns empty df, main should exit with code 1."""
    import importlib
    import scripts.run_redteam as cli

    config = tmp_path / "attack_config.yaml"
    config.write_text(yaml.dump({
        "attacks_per_vulnerability_type": 1,
        "judge_preset": "gpt-4o-mini-or",
        "attacks": [{"name": "PromptInjection", "class": "deepteam.attacks.single_turn.PromptInjection", "enabled": True}],
        "vulnerabilities": [{"name": "Toxicity", "class": "deepteam.vulnerabilities.Toxicity", "enabled": True}],
    }))
    targets = tmp_path / "targets.yaml"
    targets.write_text(yaml.dump({"targets": [{
        "name": "default", "model": "qwen/qwen-2.5-7b-instruct",
        "provider": "openrouter", "system_prompt": "You are helpful.",
    }]}))

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("RESULTS_DIR", str(tmp_path / "results"))

    empty_df = pd.DataFrame(columns=[
        "vulnerability", "owasp_id", "owasp_name", "severity",
        "pass_rate", "asr", "passed", "failed", "errored", "total",
        "attack_type", "model_version", "judge_version", "session_id",
        "timestamp", "conversations",
    ])

    with (
        patch("scripts.run_redteam.run", return_value=MagicMock()),
        patch("scripts.run_redteam.transform_risk_assessment", return_value=empty_df),
        patch("sys.argv", ["run_redteam.py", "--config", str(config), "--targets", str(targets)]),
    ):
        with pytest.raises(SystemExit) as exc_info:
            cli.main()
        assert exc_info.value.code == 1
