"""Custom LLM-as-a-Judge implementations for DeepTeam.

DeepTeam (deepeval) by default uses GPT-4o via OPENAI_API_KEY.
This module provides alternative cheap/local judge options.

Usage in runner:
    from src.red_team.judges import build_judge
    judge = build_judge(provider="openrouter", model="google/gemini-flash-1.5")
    # then pass to deepteam metrics / red_team()
"""
import os
from typing import Any

from deepeval.models import DeepEvalBaseLLM


class OpenRouterJudge(DeepEvalBaseLLM):
    """Judge that routes through OpenRouter — supports any model on the platform."""

    def __init__(self, model: str, api_key: str | None = None):
        self.model_name = model
        self._api_key = api_key or os.environ["OPENROUTER_API_KEY"]

    def get_model_name(self) -> str:
        return self.model_name

    def load_model(self) -> Any:
        from openai import OpenAI
        return OpenAI(
            api_key=self._api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def generate(self, prompt: str) -> str:
        client = self.load_model()
        response = client.chat.completions.create(
            model=self.model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(
            api_key=self._api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        response = await client.chat.completions.create(
            model=self.model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""


class OllamaJudge(DeepEvalBaseLLM):
    """Judge using a local Ollama model — completely free, no API key needed.

    Prerequisites:
        brew install ollama
        ollama pull llama3.2   # or mistral, phi3, etc.
        ollama serve           # start the server (port 11434)
    """

    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model_name = model
        self._base_url = base_url

    def get_model_name(self) -> str:
        return f"ollama/{self.model_name}"

    def load_model(self) -> Any:
        from openai import OpenAI
        return OpenAI(api_key="ollama", base_url=f"{self._base_url}/v1")

    def generate(self, prompt: str) -> str:
        client = self.load_model()
        response = client.chat.completions.create(
            model=self.model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    async def a_generate(self, prompt: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key="ollama", base_url=f"{self._base_url}/v1")
        response = await client.chat.completions.create(
            model=self.model_name,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""


# --- Preset configurations ---

JUDGE_PRESETS: dict[str, dict] = {
    # OpenAI (default deepeval judge — best quality)
    "gpt-4o":       {"provider": "openai",      "model": "gpt-4o"},
    "gpt-4o-mini":  {"provider": "openai",      "model": "gpt-4o-mini"},   # cheapest OpenAI

    # Anthropic
    "haiku":        {"provider": "anthropic",   "model": "claude-haiku-4-5-20251001"},

    # OpenRouter — cheap options
    "gemini-flash": {"provider": "openrouter",  "model": "google/gemini-2.0-flash-001"},
    "llama3-70b":   {"provider": "openrouter",  "model": "meta-llama/llama-3.3-70b-instruct"},
    "mistral-7b":   {"provider": "openrouter",  "model": "mistralai/mistral-7b-instruct"},
    "qwen-2.5-72b": {"provider": "openrouter",  "model": "qwen/qwen-2.5-72b-instruct"},
    # OpenAI via OpenRouter (reliable JSON output — recommended)
    "gpt-4o-mini-or": {"provider": "openrouter", "model": "openai/gpt-4o-mini"},
    "gpt-4o-or":      {"provider": "openrouter", "model": "openai/gpt-4o"},
    # Claude Haiku via OpenRouter
    "haiku-or":       {"provider": "openrouter", "model": "anthropic/claude-3-haiku-20240307"},

    # Local (free)
    "ollama-llama": {"provider": "ollama",      "model": "llama3.2"},
    "ollama-mistral": {"provider": "ollama",    "model": "mistral"},
    "ollama-phi":   {"provider": "ollama",      "model": "phi3"},
}


def build_judge(
    provider: str = "openai",
    model: str = "gpt-4o-mini",
    api_key: str | None = None,
    ollama_url: str = "http://localhost:11434",
) -> DeepEvalBaseLLM | None:
    """Build and return a judge instance.

    Args:
        provider:   "openai" | "openrouter" | "ollama"
                    "openai" and "anthropic" use deepeval's built-in support.
        model:      Model ID for the chosen provider.
        api_key:    Override API key (falls back to env vars).
        ollama_url: Base URL for Ollama server.

    Returns:
        DeepEvalBaseLLM instance, or None to use deepeval's default (GPT-4o).
    """
    if provider == "openrouter":
        return OpenRouterJudge(model=model, api_key=api_key)

    if provider == "ollama":
        return OllamaJudge(model=model, base_url=ollama_url)

    # For "openai" and "anthropic", deepeval handles them natively via env vars.
    # Return None to let deepeval use its default configuration.
    return None


def register_custom_presets(presets: dict[str, dict]) -> None:
    """Register custom judge presets from YAML config at runtime.

    Example YAML:
        judge_preset: my-judge
        judge_custom_presets:
          my-judge:
            provider: openrouter
            model: mistralai/mistral-small
    """
    JUDGE_PRESETS.update(presets)


def build_judge_from_preset(preset: str) -> DeepEvalBaseLLM | None:
    """Build a judge from a named preset defined in JUDGE_PRESETS."""
    if preset not in JUDGE_PRESETS:
        available = ", ".join(JUDGE_PRESETS)
        raise ValueError(f"Unknown judge preset '{preset}'. Available: {available}")
    cfg = JUDGE_PRESETS[preset]
    return build_judge(provider=cfg["provider"], model=cfg["model"])
