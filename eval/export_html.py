#!/usr/bin/env python3
"""
Export RAG quality report as standalone HTML (for browser printing).

Usage:
    python eval/export_html.py eval/results/20260418_130046_..._ragas/
    python eval/export_html.py eval/results/.../ --fail-below 0.75

Outputs HTML to stdout (for piping to Next.js API route).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

EVAL_DIR = Path(__file__).parent
TEMPLATES_DIR = EVAL_DIR / "templates"

SCORE_KEYS = [
    ("faithfulness_score",          "Faithfulness",      "Faith"),
    ("answer_relevancy_score",      "Answer Relevancy",  "Relev"),
    # RAGAS key names
    ("context_precision_score",     "Ctx Precision",     "Prec"),
    ("context_recall_score",        "Ctx Recall",        "Recall"),
    # DeepEval key names (contextual_* prefix)
    ("contextual_precision_score",  "Ctx Precision",     "Prec"),
    ("contextual_recall_score",     "Ctx Recall",        "Recall"),
    ("answer_correctness_score",    "Answer Correctness","Correct"),
    ("completeness_score",          "Completeness",      "Compl"),
]


def _build_context(results_dir: Path, fail_below: Optional[float]) -> dict:
    metrics_path = results_dir / "metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"metrics.json not found in {results_dir}")

    rows: list[dict] = json.loads(metrics_path.read_text(encoding="utf-8"))

    # Detect which score keys are actually present
    present_keys = [
        (key, label, short)
        for key, label, short in SCORE_KEYS
        if any(row.get(key) is not None for row in rows)
    ]

    # Build per-metric summaries
    metrics_summary = []
    for key, label, short in present_keys:
        values = [r[key] for r in rows if r.get(key) is not None]
        if not values:
            continue
        metrics_summary.append({
            "key": key,
            "label": label,
            "short": short,
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
        })

    overall_avg = (
        sum(m["avg"] for m in metrics_summary) / len(metrics_summary)
        if metrics_summary else 0.0
    )

    threshold = fail_below if fail_below is not None else 0.70
    gate_passed = all(m["avg"] >= threshold for m in metrics_summary)

    # Infer framework + dataset name from dir name
    dir_name = results_dir.name
    framework = "RAGAS" if "ragas" in dir_name.lower() else "DeepEval"
    dataset_name = dir_name

    return {
        "dataset_name": dataset_name,
        "framework": framework,
        "judge": "see eval/config/eval_config.yaml",
        "generated_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "total_rows": len(rows),
        "threshold": threshold,
        "overall_avg": overall_avg,
        "gate_passed": gate_passed,
        "metrics_summary": metrics_summary,
        "rows": rows,
    }


def export_html(results_dir: Path, fail_below: Optional[float] = None) -> str:
    """Render a standalone HTML report. Returns HTML string."""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: pip install jinja2"
        ) from exc

    ctx = _build_context(results_dir, fail_below)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )

    # Use same template, but inline CSS for standalone HTML
    template = env.get_template("rag_report.html")
    html_str = template.render(**ctx)

    # Read CSS and inline it into <style> tag
    css_path = TEMPLATES_DIR / "rag_report.css"
    if css_path.exists():
        css_content = css_path.read_text(encoding="utf-8")
        # Replace <link rel="stylesheet"> with inline <style>
        html_str = html_str.replace(
            '<link rel="stylesheet" href="rag_report.css">',
            f'<style>{css_content}</style>'
        )

    # Add print button script
    print_script = """
<script>
// Auto-focus and add keyboard shortcut for printing
window.addEventListener('load', () => {
    // Ctrl+P / Cmd+P already works, but add a visible button
    const printBtn = document.createElement('button');
    printBtn.textContent = '🖨️ Печать PDF';
    printBtn.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 9999;
    `;
    printBtn.onclick = () => window.print();
    document.body.appendChild(printBtn);

    // Hide print button when printing
    const style = document.createElement('style');
    style.textContent = '@media print { button { display: none !important; } }';
    document.head.appendChild(style);
});
</script>
"""
    html_str = html_str.replace('</body>', f'{print_script}</body>')

    return html_str


def main() -> None:
    parser = argparse.ArgumentParser(description="Export RAG quality HTML report (for browser printing)")
    parser.add_argument("results_dir", help="Path to results directory (contains metrics.json)")
    parser.add_argument("--fail-below", type=float, default=None,
                        help="Quality gate threshold 0–1 (default: 0.70)")
    args = parser.parse_args()

    results_dir = Path(args.results_dir).expanduser().resolve()

    try:
        html = export_html(results_dir, args.fail_below)
        print(html, end='')  # stdout for piping to Next.js
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
