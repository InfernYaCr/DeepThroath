#!/usr/bin/env python3
"""CLI entry point for red team scans. Used by CI/CD and manual runs."""
import argparse
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from dotenv import load_dotenv

load_dotenv()

from src.data.storage import save_results
from src.data.transformer import transform_risk_assessment
from src.red_team.attacks import AttackConfig, VulnerabilityConfig
from src.red_team.judges import register_custom_presets
from src.red_team.runner import run


from pydantic import BaseModel, ValidationError


class _AttackEntry(BaseModel):
    name: str
    class_: str = ""
    enabled: bool = True

    model_config = {"populate_by_name": True, "extra": "allow"}

    def model_post_init(self, __context):
        # accept both 'class' (YAML key) and 'class_' (Python attr)
        pass


class _VulnEntry(BaseModel):
    name: str
    class_: str = ""
    enabled: bool = True

    model_config = {"populate_by_name": True, "extra": "allow"}


class _AttackConfig(BaseModel):
    attacks_per_vulnerability_type: int = 1
    asr_threshold: float = 0.20
    judge_preset: str = ""
    attacks: list[dict] = []
    vulnerabilities: list[dict] = []


def _load_yaml(path: str) -> dict:
    with open(path) as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid YAML: {path} must be a mapping, got {type(data).__name__}")
    return data


def _validate_attack_config(cfg: dict, path: str) -> None:
    try:
        _AttackConfig(**cfg)
    except ValidationError as e:
        raise ValueError(f"Invalid attack config [{path}]:\n{e}") from e
    for attack in cfg.get("attacks", []):
        if "name" not in attack:
            raise ValueError(f"[{path}] Attack entry missing 'name': {attack}")
        if "class" not in attack:
            raise ValueError(f"[{path}] Attack '{attack['name']}' missing 'class' field")
    for vuln in cfg.get("vulnerabilities", []):
        if "name" not in vuln:
            raise ValueError(f"[{path}] Vulnerability entry missing 'name': {vuln}")
        if "class" not in vuln:
            raise ValueError(f"[{path}] Vulnerability '{vuln['name']}' missing 'class' field")


def _find_target(targets_path: str, name: str) -> dict:
    data = _load_yaml(targets_path)
    targets = data.get("targets", [])
    for t in targets:
        if t["name"] == name:
            return t
    available = [t["name"] for t in targets]
    raise ValueError(
        f"Target '{name}' not found in {targets_path}\n"
        f"  Available targets: {', '.join(available)}"
    )


def run_redteam_scan(
    target: str,
    num_attacks: int = 10,
    system_prompt: str | None = None,
    config_path: str = "config/attack_config.yaml",
    targets_path: str = "config/targets.yaml",
    model_override: str | None = None,
    output_dir: str | None = None,
    judge_preset: str | None = None
) -> Path:
    """
    Запуск Red Team сканирования (callable from FastAPI).

    Args:
        target: Провайдер модели (openai:gpt-4o, anthropic:claude-sonnet-4, etc.)
        num_attacks: Количество атак для генерации
        system_prompt: Кастомный system prompt
        config_path: Путь к конфигу атак
        targets_path: Путь к конфигу целей
        model_override: Переопределить модель из target
        output_dir: Переопределить RESULTS_DIR
        judge_preset: Preset судьи (gpt-4o-mini, etc.)

    Returns:
        Path к файлу с результатами (results/latest.parquet)
    """
    if output_dir:
        os.environ["RESULTS_DIR"] = output_dir

    cfg = _load_yaml(config_path)
    _validate_attack_config(cfg, config_path)

    # Register any custom judge presets from YAML
    custom_presets = cfg.get("judge_custom_presets", {})
    if custom_presets:
        register_custom_presets(custom_presets)

    # NOTE: Dynamic API config support будет добавлен при необходимости
    target_config = _find_target(targets_path, target)

    model = model_override or target_config["model"]
    sys_prompt = system_prompt or target_config.get("system_prompt", "")
    attacks_per_type = num_attacks  # используем num_attacks как attacks_per_vulnerability_type
    asr_threshold = cfg.get("asr_threshold", 0.20)

    # Parse attacks from YAML (only enabled ones)
    attack_configs = [
        AttackConfig(name=a["name"], attack_class=a["class"], enabled=a.get("enabled", True))
        for a in cfg.get("attacks", [])
        if a.get("enabled", True)
    ] or None

    # Parse vulnerabilities from YAML (only enabled ones)
    vuln_configs = [
        VulnerabilityConfig(name=v["name"], vulnerability_class=v["class"], enabled=v.get("enabled", True))
        for v in cfg.get("vulnerabilities", [])
        if v.get("enabled", True)
    ] or None

    print(f"[+] Model: {model}")
    print(f"[+] Attacks per vulnerability type: {attacks_per_type}")
    print(f"[+] Attack types: {[a.name for a in attack_configs] if attack_configs else 'default'}")
    print(f"[+] Vulnerabilities: {[v.name for v in vuln_configs] if vuln_configs else 'default'}")

    provider = target_config.get("provider", "anthropic")
    print(f"[+] Provider: {provider}")

    judge = judge_preset or cfg.get("judge_preset")
    if judge:
        print(f"[+] Judge: {judge}")
    else:
        print("[+] Judge: deepeval default (gpt-4o via OPENAI_API_KEY)")

    risk_assessment = run(
        model=model,
        system_prompt=sys_prompt,
        attacks_per_vulnerability_type=attacks_per_type,
        provider=provider,
        judge_preset=judge,
        attack_configs=attack_configs,
        vuln_configs=vuln_configs,
        api_config=None,
    )

    judge_label = judge or "deepeval-default"
    df = transform_risk_assessment(risk_assessment, model_version=model, judge_version=judge_label)

    if df.empty:
        print("\n[!] All tests errored — no results to save. Check judge model JSON output.")
        raise RuntimeError("All Red Team tests failed")

    output_path = save_results(df)

    overall_asr = float(df["asr"].mean())
    print(f"\n[+] Results saved to {output_path}")
    print(f"[+] Overall ASR: {overall_asr:.1%}")
    print(df[["vulnerability", "severity", "pass_rate", "asr"]].to_string(index=False))

    if overall_asr > asr_threshold:
        print(f"\n[!] ASR {overall_asr:.1%} exceeds threshold {asr_threshold:.0%} — FAIL")
        # Не делаем sys.exit в callable функции, только в CLI

    return Path(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM Red Team scan")
    parser.add_argument("--config", default="config/attack_config.yaml")
    parser.add_argument("--targets", default="config/targets.yaml")
    parser.add_argument("--target", default="default")
    parser.add_argument("--model", default=None, help="Override target model")
    parser.add_argument("--output", default=None, help="Override RESULTS_DIR")
    parser.add_argument(
        "--judge", default=None,
        help="Judge preset: gpt-4o-mini, gemini-flash, llama3-70b, haiku, ollama-llama, ollama-mistral, ollama-phi",
    )
    parser.add_argument("--dynamic-api-config", default=None, help="Path to dynamic API contract JSON")
    args = parser.parse_args()

    # TODO: refactor dynamic-api-config support
    if args.dynamic_api_config:
        print("[!] dynamic-api-config not yet supported in callable mode, falling back to legacy CLI flow")
        # Keep legacy flow for now
        if args.output:
            os.environ["RESULTS_DIR"] = args.output

        cfg = _load_yaml(args.config)
        _validate_attack_config(cfg, args.config)
        custom_presets = cfg.get("judge_custom_presets", {})
        if custom_presets:
            register_custom_presets(custom_presets)

        with open(args.dynamic_api_config, "r", encoding="utf-8") as f:
            api_config = json.load(f)
        target = {"model": "dynamic-api", "system_prompt": "N/A", "provider": "http"}

        model = args.model or target["model"]
        system_prompt = target.get("system_prompt", "")
        attacks_per_type = cfg.get("attacks_per_vulnerability_type", 1)
        asr_threshold = cfg.get("asr_threshold", 0.20)

        attack_configs = [
            AttackConfig(name=a["name"], attack_class=a["class"], enabled=a.get("enabled", True))
            for a in cfg.get("attacks", [])
            if a.get("enabled", True)
        ] or None

        vuln_configs = [
            VulnerabilityConfig(name=v["name"], vulnerability_class=v["class"], enabled=v.get("enabled", True))
            for v in cfg.get("vulnerabilities", [])
            if v.get("enabled", True)
        ] or None

        print(f"[+] Model: {model}")
        print(f"[+] Attacks per vulnerability type: {attacks_per_type}")
        provider = target.get("provider", "anthropic")
        print(f"[+] Provider: {provider}")

        judge_preset = args.judge or cfg.get("judge_preset")
        if judge_preset:
            print(f"[+] Judge: {judge_preset}")
        else:
            print("[+] Judge: deepeval default (gpt-4o via OPENAI_API_KEY)")

        risk_assessment = run(
            model=model,
            system_prompt=system_prompt,
            attacks_per_vulnerability_type=attacks_per_type,
            provider=provider,
            judge_preset=judge_preset,
            attack_configs=attack_configs,
            vuln_configs=vuln_configs,
            api_config=api_config,
        )

        judge_label = judge_preset or "deepeval-default"
        df = transform_risk_assessment(risk_assessment, model_version=model, judge_version=judge_label)

        if df.empty:
            print("\n[!] All tests errored — no results to save. Check judge model JSON output.")
            sys.exit(1)

        output_path = save_results(df)
        overall_asr = float(df["asr"].mean())
        print(f"\n[+] Results saved to {output_path}")
        print(f"[+] Overall ASR: {overall_asr:.1%}")

        if overall_asr > asr_threshold:
            print(f"\n[!] ASR {overall_asr:.1%} exceeds threshold {asr_threshold:.0%} — FAIL")
            sys.exit(1)

        print(f"\n[+] ASR within threshold ({asr_threshold:.0%}) — PASS")
        return

    # Use callable function
    try:
        cfg = _load_yaml(args.config)
        asr_threshold = cfg.get("asr_threshold", 0.20)

        output_path = run_redteam_scan(
            target=args.target,
            num_attacks=cfg.get("attacks_per_vulnerability_type", 1),
            system_prompt=None,
            config_path=args.config,
            targets_path=args.targets,
            model_override=args.model,
            output_dir=args.output,
            judge_preset=args.judge
        )

        # Check ASR threshold for CLI exit code
        import pandas as pd
        df = pd.read_parquet(output_path)
        overall_asr = float(df["asr"].mean())

        if overall_asr > asr_threshold:
            print(f"\n[!] ASR {overall_asr:.1%} exceeds threshold {asr_threshold:.0%} — FAIL")
            sys.exit(1)

        print(f"\n[+] ASR within threshold ({asr_threshold:.0%}) — PASS")
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
