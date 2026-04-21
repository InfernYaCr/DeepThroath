from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
    keep_trailing_newline=True,
)

_env_md = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=False,
    keep_trailing_newline=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_html_report(context: dict) -> str:
    """Render the Jinja2 HTML report template with the given context."""
    template = _env.get_template("report.html")
    return template.render(**context)


def render_markdown_report(context: dict) -> str:
    """Render the Jinja2 Markdown report template with the given context."""
    template = _env_md.get_template("report.md")
    return template.render(**context)


def export_pdf(html: str) -> bytes:
    """Convert rendered HTML to PDF bytes using WeasyPrint."""
    try:
        from weasyprint import HTML

        return HTML(string=html, base_url=str(TEMPLATES_DIR)).write_pdf()
    except ImportError as exc:
        raise RuntimeError("weasyprint is required for PDF export. Install it with: pip install weasyprint") from exc
