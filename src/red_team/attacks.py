import importlib
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AttackConfig:
    name: str
    attack_class: str
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class VulnerabilityConfig:
    name: str
    vulnerability_class: str
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


DEFAULT_ATTACKS: list[AttackConfig] = [
    AttackConfig(
        name="PromptInjection",
        attack_class="deepteam.attacks.single_turn.PromptInjection",
    ),
    AttackConfig(
        name="Roleplay",
        attack_class="deepteam.attacks.single_turn.Roleplay",
    ),
    AttackConfig(
        name="CrescendoJailbreaking",
        attack_class="deepteam.attacks.multi_turn.CrescendoJailbreaking",
    ),
    AttackConfig(
        name="LinearJailbreaking",
        attack_class="deepteam.attacks.multi_turn.LinearJailbreaking",
    ),
]

DEFAULT_VULNERABILITIES: list[VulnerabilityConfig] = [
    VulnerabilityConfig(
        name="PromptLeakage",
        vulnerability_class="deepteam.vulnerabilities.PromptLeakage",
    ),
    VulnerabilityConfig(
        name="PIILeakage",
        vulnerability_class="deepteam.vulnerabilities.PIILeakage",
    ),
    VulnerabilityConfig(
        name="ExcessiveAgency",
        vulnerability_class="deepteam.vulnerabilities.ExcessiveAgency",
    ),
    VulnerabilityConfig(
        name="Toxicity",
        vulnerability_class="deepteam.vulnerabilities.Toxicity",
    ),
    VulnerabilityConfig(
        name="Bias",
        vulnerability_class="deepteam.vulnerabilities.Bias",
    ),
    VulnerabilityConfig(
        name="IllegalActivity",
        vulnerability_class="deepteam.vulnerabilities.IllegalActivity",
    ),
]


def _load_class(class_path: str) -> type:
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def build_attacks(configs: list[AttackConfig]) -> list[Any]:
    return [_load_class(cfg.attack_class)(**cfg.params) for cfg in configs if cfg.enabled]


def build_vulnerabilities(configs: list[VulnerabilityConfig]) -> list[Any]:
    return [_load_class(cfg.vulnerability_class)(**cfg.params) for cfg in configs if cfg.enabled]
