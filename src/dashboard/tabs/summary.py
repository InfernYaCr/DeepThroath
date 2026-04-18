import pandas as pd
import streamlit as st

from src.data.eval_storage import quality_score
from src.dashboard.charts import passrate_trend
from src.dashboard.quality_charts import quality_trend_line
from src.reports.generator import calculate_security_score


def render_summary(
    sec_df,
    history_df: pd.DataFrame,
    scan_files: list,
    eval_runs: list,
    latest_eval_df,
) -> None:
    st.header("Общая сводка")

    has_security = sec_df is not None
    has_quality = latest_eval_df is not None

    sec_score = calculate_security_score(sec_df) if has_security else None
    qual_score = quality_score(latest_eval_df) if has_quality else None

    if has_security:
        total_tests = int(sec_df["total"].sum())
        total_failed = int(sec_df["failed"].sum())
        sec_asr = total_failed / total_tests if total_tests > 0 else 0.0
    else:
        sec_asr = None

    if has_quality:
        ar_pass_rate = (
            float(latest_eval_df["answer_relevancy_passed"].mean())
            if "answer_relevancy_passed" in latest_eval_df.columns
            else None
        )
    else:
        ar_pass_rate = None

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Оценка безопасности",
        f"{sec_score:.0f}/100" if sec_score is not None else "—",
        help="Комплексная оценка безопасности (0–100). Выше = лучше.",
    )
    col2.metric(
        "Оценка качества (AR)",
        f"{qual_score:.1f}/100" if qual_score is not None else "—",
        help="Средний Answer Relevancy Score × 100. Выше = лучше.",
    )
    col3.metric(
        "ASR (доля взломов)",
        f"{sec_asr:.1%}" if sec_asr is not None else "—",
        help="Attack Success Rate. Чем ниже, тем безопаснее.",
    )
    col4.metric(
        "Качество — Pass Rate",
        f"{ar_pass_rate:.1%}" if ar_pass_rate is not None else "—",
        help="Доля записей с AR Score >= порога.",
    )

    st.divider()

    col_sec, col_qual = st.columns(2)
    with col_sec:
        st.subheader("Тренд безопасности")
        if has_security and not history_df.empty:
            st.plotly_chart(passrate_trend(history_df), width="stretch")
        else:
            st.info("Нет данных по безопасности для отображения тренда.")
    with col_qual:
        st.subheader("Тренд качества RAG")
        if eval_runs:
            st.plotly_chart(quality_trend_line(list(reversed(eval_runs))), width="stretch")
        else:
            st.info("Нет данных по качеству RAG для отображения тренда.")

    st.divider()

    col_sec2, col_qual2 = st.columns(2)
    with col_sec2:
        st.subheader("Последние 5 сканов безопасности")
        if scan_files:
            st.dataframe(
                pd.DataFrame([{"Скан": s["label"]} for s in scan_files[:5]]),
                hide_index=True,
                width="stretch",
            )
        else:
            st.info("Нет истории сканирований безопасности.")
    with col_qual2:
        st.subheader("Последние 5 прогонов оценки качества")
        if eval_runs:
            rows = [
                {
                    "Прогон": r["label"].split(" | ")[0],
                    "AR Mean": f"{r['ar_mean']:.3f}",
                    "Pass Rate": f"{r['pass_rate']:.0%}",
                }
                for r in eval_runs[:5]
            ]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            st.info("Нет истории прогонов оценки качества.")

    st.divider()

    st.subheader("Общий статус системы")
    if sec_score is not None and qual_score is not None:
        combined = (sec_score + qual_score) / 2
        if combined >= 80:
            st.success(f"✅ Система в хорошем состоянии — комбинированный балл: {combined:.1f}/100")
        elif combined >= 60:
            st.warning(f"⚠️ Требует внимания — комбинированный балл: {combined:.1f}/100")
        else:
            st.error(f"🔴 Критическое состояние — комбинированный балл: {combined:.1f}/100")
    elif sec_score is not None:
        st.info(f"Нет данных качества RAG. Безопасность: {sec_score:.0f}/100")
    elif qual_score is not None:
        st.info(f"Нет данных безопасности. Качество RAG: {qual_score:.1f}/100")
    else:
        st.warning("Нет данных ни по безопасности, ни по качеству RAG.")
