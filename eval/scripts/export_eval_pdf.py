#!/usr/bin/env python3
"""
Export RAG Evaluation results to branded PDF report.

Usage:
    python eval/scripts/export_eval_pdf.py eval/results/20260421_192715_20260329_173829_exp_top_k_10_dataset

Output:
    Creates report.pdf in the results directory
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.reports.pdf_export import render_html_report, export_pdf


def calculate_overall_score(ar_avg: float | None, fa_avg: float | None,
                             cp_avg: float | None, cr_avg: float | None) -> int:
    """Calculate overall quality score (0-100) weighted by metric importance."""
    scores = []
    weights = []

    if ar_avg is not None:
        scores.append(ar_avg)
        weights.append(0.4)  # Answer Relevancy — most important

    if fa_avg is not none:
        scores.append(fa_avg)
        weights.append(0.3)  # Faithfulness — second most important

    if cp_avg is not none:
        scores.append(cp_avg)
        weights.append(0.15)  # Precision

    if cr_avg is not none:
        scores.append(cr_avg)
        weights.append(0.15)  # Recall

    if not scores:
        return 0

    # Normalize weights
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]

    weighted_avg = sum(s * w for s, w in zip(scores, weights))
    return int(weighted_avg * 100)


def load_eval_results(results_dir: Path) -> dict:
    """Load evaluation results from directory."""
    metrics_file = results_dir / "metrics.json"
    meta_file = results_dir / "meta.json"

    if not metrics_file.exists():
        raise FileNotFoundError(f"metrics.json not found in {results_dir}")

    with open(metrics_file, encoding="utf-8") as f:
        metrics = json.load(f)

    meta = {}
    if meta_file.exists():
        with open(meta_file, encoding="utf-8") as f:
            meta = json.load(f)

    return {"metrics": metrics, "meta": meta}


def prepare_context(results_dir: Path) -> dict:
    """Prepare Jinja2 context for rendering eval report."""
    data = load_eval_results(results_dir)
    metrics = data["metrics"]
    meta = data["meta"]

    # Calculate aggregated metrics
    ar_scores = [r["answer_relevancy_score"] for r in metrics if r.get("answer_relevancy_score") is not None]
    fa_scores = [r["faithfulness_score"] for r in metrics if r.get("faithfulness_score") is not None]
    cp_scores = [r.get("contextual_precision_score") for r in metrics if r.get("contextual_precision_score") is not None]
    cr_scores = [r.get("contextual_recall_score") for r in metrics if r.get("contextual_recall_score") is not None]

    def safe_avg(scores):
        return sum(scores) / len(scores) if scores else None

    def safe_pass_rate(scores, threshold):
        return sum(1 for s in scores if s >= threshold) / len(scores) if scores else 0

    ar_avg = safe_avg(ar_scores)
    fa_avg = safe_avg(fa_scores)
    cp_avg = safe_avg(cp_scores)
    cr_avg = safe_avg(cr_scores)

    # Thresholds (can be loaded from config)
    ar_threshold = 0.7
    fa_threshold = 0.8
    cp_threshold = 0.7
    cr_threshold = 0.6

    ar_pass_count = sum(1 for s in ar_scores if s >= ar_threshold) if ar_scores else 0
    fa_pass_count = sum(1 for s in fa_scores if s >= fa_threshold) if fa_scores else 0
    cp_pass_count = sum(1 for s in cp_scores if s >= cp_threshold) if cp_scores else 0
    cr_pass_count = sum(1 for s in cr_scores if s >= cr_threshold) if cr_scores else 0

    overall_score = calculate_overall_score(ar_avg, fa_avg, cp_avg, cr_avg)

    # Category statistics
    from collections import defaultdict
    category_data = defaultdict(lambda: {"count": 0, "ar_scores": [], "fa_scores": []})

    for r in metrics:
        cat = r.get("category", "Unknown")
        category_data[cat]["count"] += 1
        if r.get("answer_relevancy_score") is not None:
            category_data[cat]["ar_scores"].append(r["answer_relevancy_score"])
        if r.get("faithfulness_score") is not None:
            category_data[cat]["fa_scores"].append(r["faithfulness_score"])

    category_stats = []
    for cat, data in sorted(category_data.items()):
        category_stats.append({
            "category": cat,
            "count": data["count"],
            "ar_avg": safe_avg(data["ar_scores"]),
            "ar_pass_rate": safe_pass_rate(data["ar_scores"], ar_threshold),
            "fa_avg": safe_avg(data["fa_scores"]),
        })

    # Top records (best and worst examples)
    sorted_by_ar = sorted(
        [r for r in metrics if r.get("answer_relevancy_score") is not None],
        key=lambda x: x["answer_relevancy_score"],
        reverse=True
    )

    top_records = []
    # Take top 5 best and top 5 worst
    for r in (sorted_by_ar[:5] + sorted_by_ar[-5:]):
        top_records.append({
            "id": r.get("id", "Unknown"),
            "category": r.get("category", "Unknown"),
            "query": r.get("user_query", ""),
            "expected_answer": r.get("expected_answer", ""),
            "actual_answer": r.get("actual_answer", ""),
            "ar_score": r.get("answer_relevancy_score"),
            "ar_passed": r.get("answer_relevancy_passed", False),
            "ar_reason": r.get("answer_relevancy_reason", ""),
            "fa_score": r.get("faithfulness_score"),
            "fa_passed": r.get("faithfulness_passed", False),
            "cp_score": r.get("contextual_precision_score"),
            "cp_passed": r.get("contextual_precision_passed", False),
            "cr_score": r.get("contextual_recall_score"),
            "cr_passed": r.get("contextual_recall_passed", False),
        })

    # Build context
    dataset_name = meta.get("dataset", results_dir.name)
    if "/" in dataset_name:
        dataset_name = Path(dataset_name).name

    judge_model = meta.get("judge_model", "Unknown")
    provider = meta.get("provider", "")
    judge_version = f"{judge_model} ({provider})" if provider else judge_model

    timestamp = meta.get("timestamp", results_dir.name[:15])
    try:
        dt = datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        generated_at = dt.strftime("%d.%m.%Y %H:%M")
    except:
        generated_at = timestamp

    context = {
        # Header
        "client_name": "Внутренняя оценка качества",
        "overall_score": overall_score,
        "score_delta": None,  # TODO: compare with previous run

        # Meta
        "dataset_name": dataset_name,
        "judge_version": judge_version,
        "generated_at": generated_at,
        "total_records": len(metrics),
        "skipped_count": meta.get("total_records", len(metrics)) - len(metrics),
        "passed_count": ar_pass_count,

        # Metrics
        "ar_avg": ar_avg,
        "ar_threshold": ar_threshold,
        "ar_total": len(ar_scores),
        "ar_pass_count": ar_pass_count,
        "ar_pass_rate": safe_pass_rate(ar_scores, ar_threshold),

        "fa_avg": fa_avg,
        "fa_threshold": fa_threshold,
        "fa_total": len(fa_scores),
        "fa_pass_count": fa_pass_count,
        "fa_pass_rate": safe_pass_rate(fa_scores, fa_threshold),

        "cp_avg": cp_avg,
        "cp_threshold": cp_threshold,
        "cp_total": len(cp_scores),
        "cp_pass_count": cp_pass_count,
        "cp_pass_rate": safe_pass_rate(cp_scores, cp_threshold),

        "cr_avg": cr_avg,
        "cr_threshold": cr_threshold,
        "cr_total": len(cr_scores),
        "cr_pass_count": cr_pass_count,
        "cr_pass_rate": safe_pass_rate(cr_scores, cr_threshold),

        # Detailed data
        "category_stats": category_stats,
        "top_records": top_records,
    }

    return context


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    if not results_dir.exists():
        print(f"Error: Directory not found: {results_dir}")
        sys.exit(1)

    print(f"[+] Loading results from {results_dir}")
    context = prepare_context(results_dir)

    print(f"[+] Rendering HTML report...")
    # Use custom template for eval
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    templates_dir = Path(__file__).parent.parent.parent / "src" / "reports" / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )
    template = env.get_template("eval_report.html")
    html = template.render(**context)

    print(f"[+] Generating PDF...")
    pdf_bytes = export_pdf(html)

    output_path = results_dir / "report.pdf"
    output_path.write_bytes(pdf_bytes)

    print(f"[✓] PDF report saved to {output_path}")
    print(f"    Overall Score: {context['overall_score']}/100")
    print(f"    Answer Relevancy: {context['ar_avg'] * 100:.1f}% ({context['ar_pass_count']}/{context['ar_total']} passed)")
    if context['fa_avg'] is not None:
        print(f"    Faithfulness: {context['fa_avg'] * 100:.1f}% ({context['fa_pass_count']}/{context['fa_total']} passed)")


if __name__ == "__main__":
    main()
