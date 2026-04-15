"""Tests for src/red_team/severity.py"""
import pytest

from src.red_team.severity import (
    OWASP_REGISTRY,
    Severity,
    get_owasp_category,
)


# --- Registry completeness ---

def test_registry_has_known_vulnerabilities():
    expected = [
        "PromptInjection", "ExcessiveAgency", "PromptLeakage",
        "PIILeakage", "Toxicity", "Bias", "IllegalActivity",
        "SQLInjection", "SSRF", "ShellInjection", "BOLA", "BFLA", "RBAC",
        "ChildProtection", "Ethics", "Fairness",
    ]
    for name in expected:
        assert name in OWASP_REGISTRY, f"{name} missing from OWASP_REGISTRY"


def test_all_registry_entries_have_required_fields():
    for name, cat in OWASP_REGISTRY.items():
        assert cat.id.startswith("LLM"), f"{name}: id should start with 'LLM'"
        assert cat.name, f"{name}: name is empty"
        assert cat.description, f"{name}: description is empty"
        assert cat.remediation, f"{name}: remediation is empty"
        assert isinstance(cat.severity, Severity), f"{name}: severity is not Severity enum"


# --- get_owasp_category ---

def test_exact_match():
    cat = get_owasp_category("PromptInjection")
    assert cat.id == "LLM01"
    assert cat.severity == Severity.CRITICAL


def test_strips_type_suffix():
    """'ToxicityType' should resolve to 'Toxicity'."""
    cat = get_owasp_category("ToxicityType")
    assert cat.id == "LLM09"


def test_strips_subtype_after_dot():
    """'ToxicityType.INSULTS' → 'Toxicity'."""
    cat = get_owasp_category("ToxicityType.INSULTS")
    assert cat.id == "LLM09"
    assert cat.severity == Severity.MEDIUM


def test_pii_leakage_subtype():
    cat = get_owasp_category("PIILeakageType.DIRECT")
    assert cat.id == "LLM07"


def test_excessive_agency_subtype():
    cat = get_owasp_category("ExcessiveAgencyType.PERMISSIONS")
    assert cat.id == "LLM06"
    assert cat.severity == Severity.CRITICAL


def test_unknown_vulnerability_returns_fallback():
    cat = get_owasp_category("SomeCompletelyUnknownVulnerability")
    assert cat.id == "LLM09"
    assert cat.severity == Severity.MEDIUM
    assert cat.name == "SomeCompletelyUnknownVulnerability"


def test_unknown_subtype_returns_fallback():
    cat = get_owasp_category("UnknownType.SUBTYPE")
    assert cat.id == "LLM09"


def test_critical_severities():
    critical = ["PromptInjection", "ExcessiveAgency", "IllegalActivity",
                "SQLInjection", "ShellInjection", "SSRF", "ChildProtection",
                "PersonalSafety", "UnexpectedCodeExecution", "RecursiveHijacking",
                "ExploitToolAgent"]
    for name in critical:
        cat = get_owasp_category(name)
        assert cat.severity == Severity.CRITICAL, f"{name} should be CRITICAL"


def test_bias_subtype_medium():
    for subtype in ["BiasType.RACE", "BiasType.GENDER", "BiasType.RELIGION", "BiasType.POLITICS"]:
        cat = get_owasp_category(subtype)
        assert cat.severity == Severity.MEDIUM, f"{subtype} should be MEDIUM"
