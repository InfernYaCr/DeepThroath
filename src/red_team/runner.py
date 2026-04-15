import os
from typing import Any, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI
from deepteam.test_case import RTTurn

from src.red_team.attacks import (
    DEFAULT_ATTACKS,
    DEFAULT_VULNERABILITIES,
    AttackConfig,
    VulnerabilityConfig,
    build_attacks,
    build_vulnerabilities,
)

OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


API_TIMEOUT = 60  # seconds


def _require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(
            f"[runner] Missing required environment variable: {key}\n"
            f"  → Add it to your .env file: {key}=your_key_here"
        )
    return value


def create_anthropic_callback(
    model: str,
    system_prompt: str,
    api_key: str | None = None,
):
    """Return a sync callback wrapping a Claude model via Anthropic API."""
    client = AsyncAnthropic(api_key=api_key or _require_env("ANTHROPIC_API_KEY"))

    async def model_callback(input_text: str, messages: Optional[list[RTTurn]] = None) -> RTTurn:
        history = []
        if messages:
            for turn in messages:
                history.append({"role": turn.role, "content": turn.content})
        history.append({"role": "user", "content": input_text})

        try:
            response = await client.messages.create(
                model=model,
                max_tokens=1024,
                system=system_prompt,
                messages=history,
                timeout=API_TIMEOUT,
            )
            return RTTurn(role="assistant", content=response.content[0].text)
        except Exception as e:
            return RTTurn(role="assistant", content=f"[ERROR: {type(e).__name__}: {e}]")

    return model_callback


def create_openrouter_callback(
    model: str,
    system_prompt: str,
    api_key: str | None = None,
    site_url: str | None = None,
    site_name: str | None = None,
):
    """Return a sync callback wrapping any model via OpenRouter."""
    key = api_key or _require_env("OPENROUTER_API_KEY")
    extra_headers: dict[str, str] = {}
    if site_url:
        extra_headers["HTTP-Referer"] = site_url
    if site_name:
        extra_headers["X-Title"] = site_name

    client = AsyncOpenAI(
        api_key=key,
        base_url=OPENROUTER_BASE_URL,
        default_headers=extra_headers,
        timeout=API_TIMEOUT,
    )

    async def model_callback(input_text: str, messages: Optional[list[RTTurn]] = None) -> RTTurn:
        history = [{"role": "system", "content": system_prompt}]
        if messages:
            for turn in messages:
                history.append({"role": turn.role, "content": turn.content})
        history.append({"role": "user", "content": input_text})

        try:
            response = await client.chat.completions.create(
                model=model,
                max_tokens=1024,
                messages=history,
            )
            return RTTurn(role="assistant", content=response.choices[0].message.content or "")
        except Exception as e:
            return RTTurn(role="assistant", content=f"[ERROR: {type(e).__name__}: {e}]")

    return model_callback


def run_red_team(
    model_callback,
    attack_configs: list[AttackConfig] | None = None,
    vulnerability_configs: list[VulnerabilityConfig] | None = None,
    attacks_per_vulnerability_type: int = 1,
    evaluation_model: Any = None,
) -> Any:
    """Run DeepTeam evaluation and return RiskAssessment."""
    from deepteam import red_team

    attacks = build_attacks(attack_configs or DEFAULT_ATTACKS)
    vulnerabilities = build_vulnerabilities(vulnerability_configs or DEFAULT_VULNERABILITIES)

    kwargs: dict[str, Any] = {
        "model_callback": model_callback,
        "vulnerabilities": vulnerabilities,
        "attacks": attacks,
        "attacks_per_vulnerability_type": attacks_per_vulnerability_type,
        "ignore_errors": True,
    }
    if evaluation_model is not None:
        kwargs["evaluation_model"] = evaluation_model
        kwargs["simulator_model"] = evaluation_model  # use same model for attack generation

    return red_team(**kwargs)


def run(
    model: str,
    system_prompt: str,
    attacks_per_vulnerability_type: int = 1,
    provider: str = "anthropic",
    api_key: str | None = None,
    judge_preset: str | None = None,
    attack_configs: list[AttackConfig] | None = None,
    vuln_configs: list[VulnerabilityConfig] | None = None,
) -> Any:
    """Entry point for script/CLI usage."""
    from src.red_team.judges import build_judge_from_preset

    if provider == "openrouter":
        callback = create_openrouter_callback(model, system_prompt, api_key)
    else:
        callback = create_anthropic_callback(model, system_prompt, api_key)

    judge = build_judge_from_preset(judge_preset) if judge_preset else None

    return run_red_team(
        callback,
        attack_configs=attack_configs,
        vulnerability_configs=vuln_configs,
        attacks_per_vulnerability_type=attacks_per_vulnerability_type,
        evaluation_model=judge,
    )
