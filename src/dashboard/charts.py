import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.graph_objs import Figure

from src.red_team.severity import SEVERITY_COLORS, SEVERITY_ORDER, get_owasp_category


def overall_passrate_pie(df: pd.DataFrame) -> Figure:
    total_passed = int(df["passed"].sum())
    total_failed = int(df["failed"].sum())
    return px.pie(
        names=["Защитились", "Взломано"],
        values=[total_passed, total_failed],
        color=["Защитились", "Взломано"],
        color_discrete_map={"Защитились": "#2ECC71", "Взломано": "#FF4B4B"},
        title="Соотношение успешных и проваленных тестов (Pass Rate)",
    )


def asr_by_owasp_bar(df: pd.DataFrame) -> Figure:
    summary = (
        df.groupby(["owasp_id", "owasp_name", "severity"])
        .agg(asr=("asr", "mean"))
        .reset_index()
        .sort_values(
            "severity",
            key=lambda s: s.map({v: i for i, v in enumerate(SEVERITY_ORDER)}),
        )
    )
    summary["label"] = summary["owasp_id"] + " " + summary["owasp_name"]
    fig = px.bar(
        summary,
        x="label",
        y="asr",
        color="severity",
        color_discrete_map=SEVERITY_COLORS,
        title="ASR (Успешность атак) по категориям OWASP",
        labels={"label": "Категория риска", "asr": "% Успешных атак (ASR)", "severity": "Критичность"},
        category_orders={"severity": SEVERITY_ORDER},
        hover_data={"label": True, "asr": ":.1%", "severity": True},
    )
    fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 1])
    return fig


def passrate_trend(history_df: pd.DataFrame) -> Figure:
    if history_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Тренд безопасности (пока нет истории)")
        return fig

    df = history_df.copy()
    # Truncate ISO timestamp to date for readable X-axis (one point per scan day)
    df["scan_date"] = pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%d %H:%M")

    trend = (
        df.groupby(["scan_date", "model_version"])
        .agg(pass_rate=("pass_rate", "mean"))
        .reset_index()
        .sort_values("scan_date")
    )
    fig = px.line(
        trend,
        x="scan_date",
        y="pass_rate",
        color="model_version",
        markers=True,
        title="Тренд защиты (Pass Rate) по версиям моделей",
        labels={"scan_date": "Дата замера", "pass_rate": "% Успешных защит", "model_version": "Версия модели"},
    )
    fig.update_layout(yaxis_tickformat=".0%", yaxis_range=[0, 1])
    return fig


def severity_heatmap(df: pd.DataFrame) -> Figure:
    """Heatmap grouped by localized OWASP category names (not raw sub-types)."""
    d = df.copy()
    _owasp = d["vulnerability"].map(get_owasp_category)
    d["cat_name"] = _owasp.map(lambda c: c.name)
    d["cat_severity"] = _owasp.map(lambda c: c.severity.value)

    pivot = (
        d.groupby(["cat_severity", "cat_name"])
        .agg(asr=("asr", "mean"))
        .reset_index()
        .pivot(index="cat_severity", columns="cat_name", values="asr")
        .reindex([s for s in SEVERITY_ORDER if s in d["cat_severity"].values])
    )
    return px.imshow(
        pivot,
        color_continuous_scale=["#2ECC71", "#FFC300", "#FF4B4B"],
        title="Тепловая карта: Критичность × Категория OWASP",
        labels={"color": "ASR (взломов)", "cat_severity": "Критичность", "cat_name": "Категория"},
        zmin=0,
        zmax=1,
        text_auto=".0%",
    )
