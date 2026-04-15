"""Tests for src/reports/pdf_export.py — HTML/Markdown rendering and Jinja2 context."""
from unittest.mock import MagicMock, patch

import pytest

from src.reports.pdf_export import render_html_report, render_markdown_report


# --- Minimal valid context ---

MINIMAL_CTX = {
    "client_name": "Test Corp",
    "generated_at": "01.01.2026 12:00 UTC",
    "model_version": "qwen/qwen-2.5-7b-instruct",
    "judge_version": "gpt-4o-mini",
    "security_score": 75,
    "score_delta": None,
    "total_tests": 10,
    "total_failed": 2,
    "overall_asr": 0.2,
    "top_vulnerabilities": [],
    "owasp_results": [],
    "evidence_dialogs": [],
    "recommendations": [],
    "methodology": {"attacks": ["PromptInjection"], "vulnerabilities": ["Toxicity"], "simulations": 1},
}

OWASP_RESULT = {
    "owasp_id": "LLM01", "owasp_name": "Prompt Injection",
    "vulnerability": "PromptInjection",
    "asr": 0.5, "pass_rate": 0.5,
    "severity": "Critical",
    "passed": 1, "failed": 1, "total": 2,
    "attack_type": "PromptInjection",
}


# --- render_html_report (used internally for PDF generation) ---

def test_html_render_returns_string():
    html = render_html_report(MINIMAL_CTX)
    assert isinstance(html, str)
    assert len(html) > 100


def test_html_render_contains_client_name():
    html = render_html_report(MINIMAL_CTX)
    assert "Test Corp" in html


def test_html_render_contains_security_score():
    html = render_html_report(MINIMAL_CTX)
    assert "75" in html


def test_html_render_with_owasp_results():
    ctx = {**MINIMAL_CTX, "owasp_results": [OWASP_RESULT]}
    html = render_html_report(ctx)
    assert "LLM01" in html


# --- render_markdown_report ---

def test_md_render_returns_string():
    md = render_markdown_report(MINIMAL_CTX)
    assert isinstance(md, str)
    assert len(md) > 100


def test_md_render_contains_client_name():
    md = render_markdown_report(MINIMAL_CTX)
    assert "Test Corp" in md


def test_md_render_contains_security_score():
    md = render_markdown_report(MINIMAL_CTX)
    assert "75" in md


def test_md_render_contains_model_version():
    md = render_markdown_report(MINIMAL_CTX)
    assert "qwen/qwen-2.5-7b-instruct" in md


def test_md_render_score_delta_none_no_crash():
    md = render_markdown_report({**MINIMAL_CTX, "score_delta": None})
    assert "Test Corp" in md


def test_md_render_score_delta_positive():
    md = render_markdown_report({**MINIMAL_CTX, "score_delta": 5})
    assert "+5" in md


def test_md_render_score_delta_negative():
    md = render_markdown_report({**MINIMAL_CTX, "score_delta": -3})
    assert "-3" in md


def test_md_render_with_owasp_results():
    ctx = {**MINIMAL_CTX, "owasp_results": [OWASP_RESULT]}
    md = render_markdown_report(ctx)
    assert "LLM01" in md
    assert "Prompt Injection" in md


def test_md_render_with_recommendations():
    ctx = {**MINIMAL_CTX, "recommendations": [
        {"owasp_id": "LLM09", "vulnerability": "Toxicity", "asr": 1.0,
         "severity": "Medium", "remediation": "Add content filters"}
    ]}
    md = render_markdown_report(ctx)
    assert "LLM09" in md
    assert "Add content filters" in md


def test_md_render_is_valid_markdown_structure():
    md = render_markdown_report(MINIMAL_CTX)
    assert "# " in md        # has h1
    assert "## " in md       # has h2
    assert "| " in md        # has table


def test_md_render_no_html_tags():
    md = render_markdown_report(MINIMAL_CTX)
    assert "<div" not in md
    assert "<span" not in md
    assert "<table" not in md


# --- export_pdf ---

def test_export_pdf_raises_when_weasyprint_missing():
    from src.reports.pdf_export import export_pdf
    with patch.dict("sys.modules", {"weasyprint": None}):
        with pytest.raises((RuntimeError, ImportError)):
            export_pdf("<html><body>test</body></html>")


def test_export_pdf_calls_weasyprint():
    from src.reports.pdf_export import export_pdf
    mock_html_cls = MagicMock()
    mock_html_cls.return_value.write_pdf.return_value = b"%PDF-fake"
    with patch.dict("sys.modules", {"weasyprint": MagicMock(HTML=mock_html_cls)}):
        result = export_pdf("<html><body>test</body></html>")
    assert result == b"%PDF-fake"
    mock_html_cls.assert_called_once()
