"""Plotly chart functions for RAG quality evaluation data."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import Figure


def _score_color(score: float) -> str:
    """Return a hex color for a score in [0, 1]."""
    if score >= 0.7:
        return "#2ECC71"
    if score >= 0.5:
        return "#FFC300"
    return "#FF4B4B"


def ar_by_category_bar(df: pd.DataFrame) -> Figure:
    """Horizontal bar chart: AR score per category, colored by score level."""
    if df.empty or "answer_relevancy_score" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Answer Relevancy по категориям (нет данных)")
        return fig

    col_cat = "category" if "category" in df.columns else None
    if col_cat is None:
        # No category column — show overall
        mean_score = float(df["answer_relevancy_score"].dropna().mean())
        fig = go.Figure(go.Bar(
            x=[mean_score],
            y=["Все"],
            orientation="h",
            marker_color=[_score_color(mean_score)],
        ))
        fig.update_layout(
            title="Answer Relevancy (общий)",
            xaxis=dict(range=[0, 1], tickformat=".0%"),
        )
        return fig

    summary = (
        df.groupby("category")["answer_relevancy_score"]
        .mean()
        .dropna()
        .reset_index()
        .rename(columns={"answer_relevancy_score": "ar_mean"})
        .sort_values("ar_mean")
    )

    colors = [_score_color(v) for v in summary["ar_mean"]]

    fig = go.Figure(go.Bar(
        x=summary["ar_mean"],
        y=summary["category"],
        orientation="h",
        marker_color=colors,
        text=summary["ar_mean"].map("{:.3f}".format),
        textposition="outside",
    ))
    fig.update_layout(
        title="Answer Relevancy по категориям",
        xaxis=dict(title="AR Score", range=[0, 1.05], tickformat=".0%"),
        yaxis=dict(title="Категория"),
        height=max(300, 50 * len(summary) + 100),
    )
    return fig


def ar_distribution_histogram(df: pd.DataFrame, category: str | None = None) -> Figure:
    """Score distribution histogram, optionally filtered by category."""
    if df.empty or "answer_relevancy_score" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Распределение AR Score (нет данных)")
        return fig

    data = df.copy()
    if category is not None and "category" in data.columns:
        data = data[data["category"] == category]

    scores = data["answer_relevancy_score"].dropna()
    title = f"Распределение AR Score" + (f" — {category}" if category else "")

    fig = go.Figure(go.Histogram(
        x=scores,
        nbinsx=20,
        marker_color="#3498DB",
        marker_line_color="#1A5276",
        marker_line_width=1,
    ))
    fig.add_vline(x=0.7, line_dash="dash", line_color="#E74C3C",
                  annotation_text="Порог 0.7", annotation_position="top right")
    fig.update_layout(
        title=title,
        xaxis=dict(title="AR Score", range=[0, 1]),
        yaxis=dict(title="Количество записей"),
    )
    return fig


def quality_trend_line(runs: list[dict]) -> Figure:
    """AR trend over multiple eval runs (line chart)."""
    if not runs:
        fig = go.Figure()
        fig.update_layout(title="Тренд качества RAG (пока нет данных)")
        return fig

    labels = [r["label"].split(" | ")[0] for r in runs]
    ar_means = [r["ar_mean"] for r in runs]
    pass_rates = [r["pass_rate"] for r in runs]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=labels,
        y=ar_means,
        mode="lines+markers",
        name="AR Score (среднее)",
        line=dict(color="#3498DB", width=2),
        marker=dict(size=8),
    ))
    fig.add_trace(go.Scatter(
        x=labels,
        y=pass_rates,
        mode="lines+markers",
        name="Pass Rate",
        line=dict(color="#2ECC71", width=2, dash="dot"),
        marker=dict(size=8),
    ))
    fig.add_hline(y=0.7, line_dash="dash", line_color="#E74C3C",
                  annotation_text="Порог 0.7", annotation_position="top right")
    fig.update_layout(
        title="Тренд качества RAG по прогонам",
        xaxis=dict(title="Прогон"),
        yaxis=dict(title="Score", range=[0, 1], tickformat=".0%"),
    )
    return fig


def faithfulness_vs_relevancy_scatter(df: pd.DataFrame) -> Figure:
    """Scatter: faithfulness vs answer_relevancy, colored by category."""
    if df.empty or "answer_relevancy_score" not in df.columns or "faithfulness_score" not in df.columns:
        fig = go.Figure()
        fig.update_layout(title="Faithfulness vs Answer Relevancy (нет данных)")
        return fig

    data = df.dropna(subset=["answer_relevancy_score", "faithfulness_score"]).copy()
    if data.empty:
        fig = go.Figure()
        fig.update_layout(title="Faithfulness vs Answer Relevancy (нет данных с faithfulness)")
        return fig

    color_col = "category" if "category" in data.columns else None

    fig = px.scatter(
        data,
        x="answer_relevancy_score",
        y="faithfulness_score",
        color=color_col,
        hover_data=["user_query"] if "user_query" in data.columns else None,
        title="Faithfulness vs Answer Relevancy",
        labels={
            "answer_relevancy_score": "Answer Relevancy",
            "faithfulness_score": "Faithfulness",
            "category": "Категория",
        },
        opacity=0.7,
    )
    fig.add_hline(y=0.7, line_dash="dash", line_color="#E74C3C", annotation_text="FA порог")
    fig.add_vline(x=0.7, line_dash="dash", line_color="#E74C3C", annotation_text="AR порог")
    fig.update_layout(
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
    )
    return fig
