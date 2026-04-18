import json
from datetime import datetime

import pandas as pd
import streamlit as st

from src.dashboard.quality_charts import (
    ar_by_category_bar,
    ar_distribution_histogram,
    faithfulness_vs_relevancy_scatter,
    quality_trend_line,
)


def render_quality(
    latest_eval_df,
    has_quality: bool,
    eval_runs: list,
) -> None:
    st.header("Анализ качества RAG")

    if not has_quality:
        st.warning(
            "Результаты оценки не найдены. Сначала запустите оценку:\n"
            "```bash\npython eval/scripts/run_eval.py --input <путь_к_данным.json>\n```"
        )
        st.stop()

    eval_df = latest_eval_df
    if eval_runs:
        all_run_labels = ["📌 Последний прогон"] + [r["label"] for r in eval_runs]
        sel_run_idx = st.selectbox(
            "📂 Выбор прогона",
            options=range(len(all_run_labels)),
            format_func=lambda i: all_run_labels[i],
            key="eval_run",
        )
        if sel_run_idx > 0:
            eval_df = eval_runs[sel_run_idx - 1]["df"]
            st.caption(f"Просматривается: **{all_run_labels[sel_run_idx]}**")

    st.divider()

    qtab1, qtab2, qtab3, qtab4 = st.tabs(["Обзор", "По категориям", "Детали записей", "Тренд"])

    with qtab1:
        _render_quality_overview(eval_df)

    with qtab2:
        _render_quality_categories(eval_df)

    with qtab3:
        _render_quality_details(eval_df)

    with qtab4:
        if eval_runs:
            st.plotly_chart(quality_trend_line(list(reversed(eval_runs))), width="stretch")
        else:
            st.info("Нет данных по нескольким прогонам для отображения тренда.")

    st.divider()
    _render_quality_export(eval_df)


def _render_quality_overview(eval_df: pd.DataFrame) -> None:
    ar_scores = eval_df["answer_relevancy_score"].dropna() if "answer_relevancy_score" in eval_df.columns else pd.Series(dtype=float)
    fa_scores = eval_df["faithfulness_score"].dropna() if "faithfulness_score" in eval_df.columns else pd.Series(dtype=float)
    ar_passed = eval_df["answer_relevancy_passed"] if "answer_relevancy_passed" in eval_df.columns else pd.Series(dtype=bool)

    ar_mean = float(ar_scores.mean()) if not ar_scores.empty else 0.0
    fa_mean = float(fa_scores.mean()) if not fa_scores.empty else None
    pass_rate_val = float(ar_passed.mean()) if not ar_passed.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("AR Score (среднее)", f"{ar_mean:.3f}", help="Средний Answer Relevancy Score")
    c2.metric(
        "Faithfulness Score",
        f"{fa_mean:.3f}" if fa_mean is not None else "—",
        help="Средний Faithfulness Score (только записи с контекстом)",
    )
    c3.metric("Pass Rate", f"{pass_rate_val:.1%}", help="Доля записей с AR >= порога")
    c4.metric("Записей", len(eval_df), help="Всего записей в прогоне")

    st.divider()

    col_ar, col_fa = st.columns(2)
    with col_ar:
        st.plotly_chart(ar_by_category_bar(eval_df), width="stretch")
    with col_fa:
        if not fa_scores.empty:
            st.plotly_chart(faithfulness_vs_relevancy_scatter(eval_df), width="stretch")
        else:
            st.info("Нет данных Faithfulness (поле retrieval_context отсутствует или пусто).")


def _render_quality_categories(eval_df: pd.DataFrame) -> None:
    if "category" not in eval_df.columns:
        st.info("Поле 'category' отсутствует в данных.")
        return

    for cat in sorted(eval_df["category"].dropna().unique()):
        cat_df = eval_df[eval_df["category"] == cat]
        ar_cat = cat_df["answer_relevancy_score"].dropna() if "answer_relevancy_score" in cat_df.columns else pd.Series(dtype=float)
        ar_cat_mean = float(ar_cat.mean()) if not ar_cat.empty else 0.0
        ar_cat_pass = float(cat_df["answer_relevancy_passed"].mean()) if "answer_relevancy_passed" in cat_df.columns else 0.0

        with st.expander(f"**{cat}** — AR={ar_cat_mean:.3f} | Pass={ar_cat_pass:.0%} | Записей={len(cat_df)}"):
            col_info, col_hist = st.columns([1, 2])
            with col_info:
                st.metric("AR Mean", f"{ar_cat_mean:.3f}")
                st.metric("Pass Rate", f"{ar_cat_pass:.0%}")
                st.metric("Записей", len(cat_df))
            with col_hist:
                st.plotly_chart(ar_distribution_histogram(eval_df, category=cat), width="stretch")


def _render_quality_details(eval_df: pd.DataFrame) -> None:
    st.subheader("Фильтры")
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        if "category" in eval_df.columns:
            all_cats = sorted(eval_df["category"].dropna().unique().tolist())
            sel_cats = st.multiselect("Категория", all_cats, default=all_cats, key="detail_cat")
        else:
            sel_cats = None

    with filter_col2:
        score_threshold = st.slider(
            "Минимальный AR Score",
            min_value=0.0, max_value=1.0, value=0.0, step=0.05,
            key="detail_threshold",
        )

    with filter_col3:
        pass_filter = st.radio(
            "Результат", ["Все", "Только pass", "Только fail"],
            index=0, key="detail_pass",
        )

    filtered_eval = eval_df.copy()
    if sel_cats is not None and "category" in filtered_eval.columns:
        filtered_eval = filtered_eval[filtered_eval["category"].isin(sel_cats)]
    if "answer_relevancy_score" in filtered_eval.columns:
        filtered_eval = filtered_eval[filtered_eval["answer_relevancy_score"].fillna(0) >= score_threshold]
    if pass_filter == "Только pass" and "answer_relevancy_passed" in filtered_eval.columns:
        filtered_eval = filtered_eval[filtered_eval["answer_relevancy_passed"] == True]  # noqa: E712
    elif pass_filter == "Только fail" and "answer_relevancy_passed" in filtered_eval.columns:
        filtered_eval = filtered_eval[filtered_eval["answer_relevancy_passed"] == False]  # noqa: E712

    PAGE_SIZE = 50
    total_filtered = len(filtered_eval)
    total_pages = max(1, (total_filtered + PAGE_SIZE - 1) // PAGE_SIZE)
    page = st.number_input("Страница", min_value=1, max_value=total_pages, value=1, step=1, key="detail_page") - 1
    paged_eval = filtered_eval.iloc[page * PAGE_SIZE:(page + 1) * PAGE_SIZE]

    st.caption(f"Отображено {page * PAGE_SIZE + 1}–{min((page + 1) * PAGE_SIZE, total_filtered)} из {total_filtered} записей")

    display_cols = [
        c for c in ["session_id", "category", "intent", "answer_relevancy_score",
                    "answer_relevancy_passed", "faithfulness_score", "faithfulness_passed"]
        if c in paged_eval.columns
    ]
    st.dataframe(paged_eval[display_cols], hide_index=True, width="stretch")

    st.subheader("Детали записей")
    for _, row in paged_eval.iterrows():
        ar_val = row.get("answer_relevancy_score")
        ar_passed_val = row.get("answer_relevancy_passed", False)
        icon = "✅" if ar_passed_val else "❌"
        ar_str = f"{ar_val:.3f}" if ar_val is not None else "—"
        with st.expander(f"{icon} Session {row.get('session_id', '—')} — {row.get('category', '—')} | AR={ar_str}"):
            st.markdown(f"**Вопрос:** {row.get('user_query', '—')}")
            st.markdown("**Ожидаемый ответ:**")
            st.code(row.get("expected_answer") or "—")
            st.markdown("**Ответ бота:**")
            st.code(row.get("actual_answer") or "—")
            fa_val = row.get("faithfulness_score")
            st.markdown(
                f"**AR Score:** {ar_str} | **Faithfulness:** {f'{fa_val:.3f}' if fa_val is not None else '—'}"
            )
            reason = row.get("answer_relevancy_reason")
            if reason:
                st.markdown(f"**Причина оценки AR:** {reason}")


def _render_quality_export(eval_df: pd.DataFrame) -> None:
    st.subheader("📦 Экспорт данных качества")
    col_dl_json, col_dl_md = st.columns(2)

    with col_dl_json:
        json_bytes = json.dumps(eval_df.to_dict(orient="records"), ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="⬇️ Скачать JSON (все записи)",
            data=json_bytes,
            file_name=f"eval_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
        )

    with col_dl_md:
        if st.button("📝 Сгенерировать Markdown-отчет по качеству"):
            with st.spinner("Формирование отчёта..."):
                ar_scores_md = eval_df["answer_relevancy_score"].dropna() if "answer_relevancy_score" in eval_df.columns else pd.Series(dtype=float)
                fa_scores_md = eval_df["faithfulness_score"].dropna() if "faithfulness_score" in eval_df.columns else pd.Series(dtype=float)
                ar_mean_md = float(ar_scores_md.mean()) if not ar_scores_md.empty else 0.0
                fa_mean_md = float(fa_scores_md.mean()) if not fa_scores_md.empty else None
                pass_rate_md = float(eval_df["answer_relevancy_passed"].mean()) if "answer_relevancy_passed" in eval_df.columns else 0.0

                lines = [
                    f"# Отчёт по качеству RAG — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    "",
                    "## Общий результат",
                    "",
                    "| Метрика | Значение |",
                    "|---|---|",
                    f"| Answer Relevancy (среднее) | {ar_mean_md:.3f} |",
                    f"| Faithfulness (среднее) | {fa_mean_md:.3f if fa_mean_md is not None else '—'} |",
                    f"| Pass Rate | {pass_rate_md:.1%} |",
                    f"| Всего записей | {len(eval_df)} |",
                    "",
                ]
                md_report = "\n".join(lines)
                st.download_button(
                    label="⬇️ Скачать Markdown",
                    data=md_report.encode("utf-8-sig"),
                    file_name=f"eval_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown; charset=utf-8",
                )
                st.success("✅ Markdown-отчет готов!")
