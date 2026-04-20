"""
Branded PDF export for RAG quality reports.

Usage:
    # Export from a specific results dir:
    python eval/export_pdf.py eval/results/20260418_130046_..._ragas/

    # Output to a specific path:
    python eval/export_pdf.py eval/results/.../ --out report.pdf

    # Use a custom fail threshold for gate badge:
    python eval/export_pdf.py eval/results/.../ --fail-below 0.75
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
    ("faithfulness_score", "Faithfulness", "Faith"),
    ("answer_relevancy_score", "Answer Relevancy", "Relev"),
    ("context_precision_score", "Ctx Precision", "Prec"),
    ("context_recall_score", "Ctx Recall", "Recall"),
    ("answer_correctness_score", "Answer Correctness", "Correct"),
    ("completeness_score", "Completeness", "Compl"),
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


def export_pdf(results_dir: Path, out_path: Optional[Path] = None,
               fail_below: Optional[float] = None) -> Path:
    """Render a branded PDF report and save it. Returns the output path."""
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
        from weasyprint import HTML
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency: pip install jinja2 weasyprint"
        ) from exc

    ctx = _build_context(results_dir, fail_below)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )
    html_str = env.get_template("rag_report.html").render(**ctx)
    pdf_bytes = HTML(string=html_str, base_url=str(TEMPLATES_DIR)).write_pdf()

    if out_path is None:
        out_path = results_dir / "report.pdf"

    out_path.write_bytes(pdf_bytes)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Export branded RAG quality PDF report")
    parser.add_argument("results_dir", help="Path to results directory (contains metrics.json)")
    parser.add_argument("--out", default=None, help="Output PDF path (default: <results_dir>/report.pdf)")
    parser.add_argument("--fail-below", type=float, default=None,
                        help="Quality gate threshold 0–1 (default: 0.70)")
    args = parser.parse_args()

    results_dir = Path(args.results_dir).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve() if args.out else None

    try:
        pdf_path = export_pdf(results_dir, out_path, args.fail_below)
        print(f"[OK] PDF saved → {pdf_path}")
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
