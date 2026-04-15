import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from datetime import datetime

import pandas as pd
import streamlit as st

from src.data.storage import load_history, load_latest, list_scan_files
from src.data.eval_storage import list_eval_runs, load_latest_eval, quality_score
from src.dashboard.charts import (
    asr_by_owasp_bar,
    overall_passrate_pie,
    passrate_trend,
    severity_heatmap,
)
from src.dashboard.quality_charts import (
    ar_by_category_bar,
    ar_distribution_histogram,
    faithfulness_vs_relevancy_scatter,
    quality_trend_line,
)
from src.dashboard.logs_table import render_logs_table
from src.red_team.severity import get_owasp_category, SEVERITY_BADGE, SEVERITY_ORDER, SEVERITY_COLORS
from src.reports.generator import build_report_context, calculate_security_score
from src.reports.pdf_export import render_html_report, render_markdown_report, export_pdf

st.set_page_config(
    page_title="DeepThroath + Eval — Единый дашборд",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 DeepThroath + Eval — Единый дашборд безопасности и качества LLM")


# ── Кэшированные загрузчики ────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def _cached_load_history():
    return load_history()

@st.cache_data(ttl=60)
def _cached_list_scan_files():
    return list_scan_files()

@st.cache_data(ttl=60)
def _cached_list_eval_runs():
    return list_eval_runs()

@st.cache_data(ttl=60)
def _cached_load_latest_eval():
    return load_latest_eval()


# ── Загрузка данных ────────────────────────────────────────────────────────────

with st.spinner("Загрузка данных..."):
    sec_df = load_latest()
    history_df = _cached_load_history()
    scan_files = _cached_list_scan_files()
    eval_runs = _cached_list_eval_runs()
    latest_eval_df = _cached_load_latest_eval()

has_security = sec_df is not None
has_quality = latest_eval_df is not None


# ── Навигация ──────────────────────────────────────────────────────────────────

section = st.sidebar.radio(
    "Раздел",
    ["📊 Сводка", "🔐 Безопасность", "✅ Качество RAG"],
)
st.sidebar.divider()
st.sidebar.caption("DeepThroath + Eval Dashboard")


# ══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ: СВОДКА
# ══════════════════════════════════════════════════════════════════════════════

if section == "📊 Сводка":
    st.header("Общая сводка")

    # KPI row
    sec_score = calculate_security_score(sec_df) if has_security else None
    qual_score = quality_score(latest_eval_df) if has_quality else None

    if has_security:
        total_tests = int(sec_df["total"].sum())
        total_failed = int(sec_df["failed"].sum())
        sec_asr = total_failed / total_tests if total_tests > 0 else 0.0
    else:
        sec_asr = None

    if has_quality:
        ar_pass_rate = float(latest_eval_df["answer_relevancy_passed"].mean()) if "answer_relevancy_passed" in latest_eval_df.columns else None
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

    # Side-by-side trend charts
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
            # Reverse for chronological order
            st.plotly_chart(quality_trend_line(list(reversed(eval_runs))), width="stretch")
        else:
            st.info("Нет данных по качеству RAG для отображения тренда.")

    st.divider()

    # Last 5 scans tables
    col_sec2, col_qual2 = st.columns(2)
    with col_sec2:
        st.subheader("Последние 5 сканов безопасности")
        if scan_files:
            rows = []
            for s in scan_files[:5]:
                rows.append({"Скан": s["label"]})
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            st.info("Нет истории сканирований безопасности.")
    with col_qual2:
        st.subheader("Последние 5 прогонов оценки качества")
        if eval_runs:
            rows = []
            for r in eval_runs[:5]:
                rows.append({
                    "Прогон": r["label"].split(" | ")[0],
                    "AR Mean": f"{r['ar_mean']:.3f}",
                    "Pass Rate": f"{r['pass_rate']:.0%}",
                })
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        else:
            st.info("Нет истории прогонов оценки качества.")

    st.divider()

    # Combined health indicator
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


# ══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ: БЕЗОПАСНОСТЬ
# ══════════════════════════════════════════════════════════════════════════════

elif section == "🔐 Безопасность":
    st.header("Анализ безопасности LLM")

    if not has_security:
        st.warning(
            "Результаты не найдены. Сначала запустите тестирование:\n"
            "```bash\npython scripts/run_redteam.py\n```"
        )
        st.stop()

    # --- Global scan selector ---
    df = sec_df  # default
    if scan_files:
        all_labels = ["📌 Последний скан"] + [s["label"] for s in scan_files]
        sel_idx = st.selectbox(
            "📂 Выбор скана",
            options=range(len(all_labels)),
            format_func=lambda i: all_labels[i],
            key="sec_scan",
        )
        if sel_idx > 0:
            df = scan_files[sel_idx - 1]["df"]
            st.caption(f"Просматривается: **{all_labels[sel_idx]}**")

    st.divider()

    # --- KPI row ---
    score = calculate_security_score(df)
    total_tests = int(df["total"].sum())
    total_failed = int(df["failed"].sum())
    overall_asr = total_failed / total_tests if total_tests > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Оценка безопасности", f"{score}/100", help="Комплексная оценка от 0 до 100 на основе доли успешных защит с учетом критичности уязвимостей (OWASP).")
    col2.metric("Общий ASR", f"{overall_asr:.1%}", help="Attack Success Rate (Доля успешных атак). Показывает, в каком проценте случаев атакующему удалось взломать систему. Чем ниже, тем лучше.")
    col3.metric("Всего тестов", total_tests, help="Общее количество запущенных симуляций атак.")
    col4.metric("Провалено тестов", total_failed, help="Количество тестов, в которых модель поддалась на атаку (взломана).")

    model_version = df["model_version"].iloc[0] if "model_version" in df.columns else "N/A"
    judge_version = df["judge_version"].iloc[0] if "judge_version" in df.columns else "N/A"
    scan_date = df["timestamp"].iloc[0][:16].replace("T", " ") if "timestamp" in df.columns else "N/A"

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.info(f"**Тестируемая модель:** {model_version}")
    col_m2.info(f"**Модель-судья:** {judge_version}")
    col_m3.info(f"**Дата отчета:** {scan_date}")

    st.divider()

    # --- Tabs ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Обзор", "По категориям OWASP", "Тренд", "Сравнение", "Логи атак"])

    with tab1:
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.plotly_chart(overall_passrate_pie(df), width='stretch')

        with col_right:
            st.subheader("📋 Статус по категориям OWASP")

            cat_map: dict = {}
            for _, row in df.iterrows():
                cat = get_owasp_category(row["vulnerability"])
                key = cat.id
                if key not in cat_map or row["asr"] > cat_map[key]["asr"]:
                    cat_map[key] = {
                        "id": cat.id, "name": cat.name,
                        "severity": cat.severity.value, "asr": row["asr"],
                    }
            cats_sorted = sorted(
                cat_map.values(),
                key=lambda x: (SEVERITY_ORDER.index(x["severity"]) if x["severity"] in SEVERITY_ORDER else 9, -x["asr"]),
            )
            for c in cats_sorted:
                badge = SEVERITY_BADGE.get(c["severity"], "⚪")
                if c["asr"] == 0:
                    icon, color = "✅", "green"
                elif c["asr"] >= 0.5:
                    icon, color = "🔴", "red"
                else:
                    icon, color = "🟡", "orange"
                st.markdown(
                    f"{icon} **[{c['id']}] {c['name']}** {badge}  \n"
                    f"&nbsp;&nbsp;&nbsp;Взломов: **{c['asr']:.0%}** | Защита: **{1-c['asr']:.0%}**"
                )

        st.divider()

        failed_cats = [c for c in cats_sorted if c["asr"] > 0]
        if failed_cats:
            st.subheader("⚠️ Требует внимания")
            for c in failed_cats[:5]:
                cat_full = next((get_owasp_category(v) for v in df["vulnerability"] if get_owasp_category(v).id == c["id"]), None)
                with st.expander(f"{SEVERITY_BADGE.get(c['severity'], '')} [{c['id']}] {c['name']} — взломов: {c['asr']:.0%}"):
                    if cat_full:
                        st.markdown(f"**Риск:** {cat_full.description}")
                        st.markdown(f"**Как исправить:** {cat_full.remediation}")
        else:
            st.success("✅ Все категории успешно отразили атаки в этом наборе тестов.")

    with tab2:
        with st.expander("ℹ️ Что такое OWASP LLM Top 10?"):
            st.markdown("""
**OWASP LLM Top 10** — международный стандарт безопасности для языковых моделей (2025).
Каждая уязвимость в отчёте привязана к одной из категорий:

| ID | Категория | Что проверяется |
|----|-----------|----------------|
| **LLM01** | Prompt Injection | Обход инструкций через манипуляцию промптом |
| **LLM02** | Sensitive Information Disclosure | SQL/Shell-инъекции, SSRF, выполнение кода через LLM |
| **LLM03** | Supply Chain | Скомпрометированные модели, плагины, зависимости |
| **LLM04** | Data & Model Poisoning | Отравление обучающих данных |
| **LLM05** | Improper Output Handling | Небезопасная передача ответов модели в другие системы |
| **LLM06** | Excessive Agency | Избыточные права агента, BOLA/BFLA, agentic-атаки |
| **LLM07** | System Prompt Leakage | Утечка системного промпта, конфигурации, PII |
| **LLM08** | Vector & Embedding Weaknesses | Атаки на RAG и векторные базы данных |
| **LLM09** | Misinformation | Токсичность, предвзятость, дезинформация, контент-риски |
| **LLM10** | Unbounded Consumption | DoS через неограниченное потребление токенов/ресурсов |

Подробнее: [owasp.org/www-project-top-10-for-large-language-model-applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
            """)

        st.plotly_chart(asr_by_owasp_bar(df), width='stretch')

        st.subheader("🛡️ Детальный анализ и рекомендации")
        st.info("Ниже приведены подробные описания найденных рисков и шаги по их устранению.")

        sorted_df = df.sort_values(["asr", "severity"], ascending=[False, True])

        for _, row in sorted_df.iterrows():
            vuln_name = row["vulnerability"]
            cat = get_owasp_category(vuln_name)
            asr_val = row["asr"]
            badge = SEVERITY_BADGE.get(row["severity"], "⚪")

            status_icon = "🔴" if asr_val > 0.2 else ("🟡" if asr_val > 0 else "🟢")
            label = f"{status_icon} [{cat.id}] {cat.name} | ASR: {asr_val:.1%} | {badge} {row['severity']}"

            with st.expander(label):
                col_info, col_metrics = st.columns([3, 1])
                with col_info:
                    st.markdown(f"**Описание риска:**  \n{cat.description}")
                    st.markdown(f"**🛡️ Как исправить (Ремедиация):**  \n{cat.remediation}")
                with col_metrics:
                    st.metric("Успешных атак", row["failed"])
                    st.metric("Всего попыток", row["total"])
                    pass_rate = 1.0 - asr_val
                    st.progress(pass_rate, text=f"Защита: {pass_rate:.1%}")

    with tab3:
        st.plotly_chart(passrate_trend(history_df), width='stretch')

    with tab4:
        if not scan_files or len(scan_files) < 2:
            st.info("Для сравнения нужно минимум 2 скана. Запустите ещё один скан и вернитесь.")
        else:
            all_scan_labels = [s["label"] for s in scan_files]

            col_a, col_b = st.columns(2)
            with col_a:
                idx_a = st.selectbox("Скан A (базовый)", range(len(all_scan_labels)),
                                     format_func=lambda i: all_scan_labels[i], key="cmp_a")
            with col_b:
                idx_b = st.selectbox("Скан B (новый)", range(len(all_scan_labels)),
                                     format_func=lambda i: all_scan_labels[i],
                                     index=min(1, len(all_scan_labels) - 1), key="cmp_b")

            if idx_a == idx_b:
                st.warning("Выберите два разных скана.")
            else:
                df_a = scan_files[idx_a]["df"].set_index("vulnerability")
                df_b = scan_files[idx_b]["df"].set_index("vulnerability")

                all_vulns = sorted(set(df_a.index) | set(df_b.index))

                rows = []
                for v in all_vulns:
                    asr_a = float(df_a.loc[v, "asr"]) if v in df_a.index else None
                    asr_b = float(df_b.loc[v, "asr"]) if v in df_b.index else None
                    if asr_a is not None and asr_b is not None:
                        delta = asr_b - asr_a
                        if delta < -0.01:
                            trend = "✅ улучшилось"
                        elif delta > 0.01:
                            trend = "🔴 ухудшилось"
                        else:
                            trend = "➡️ без изменений"
                    elif asr_a is None:
                        delta = None
                        trend = "🆕 новый тест"
                    else:
                        delta = None
                        trend = "➖ отсутствует в B"
                    rows.append({
                        "Уязвимость": v,
                        "ASR (A)": f"{asr_a:.1%}" if asr_a is not None else "—",
                        "ASR (B)": f"{asr_b:.1%}" if asr_b is not None else "—",
                        "Δ": f"{delta:+.1%}" if delta is not None else "—",
                        "Итог": trend,
                    })

                cmp_df = pd.DataFrame(rows)

                improved = sum(1 for r in rows if r["Итог"] == "✅ улучшилось")
                worsened = sum(1 for r in rows if r["Итог"] == "🔴 ухудшилось")
                unchanged = sum(1 for r in rows if r["Итог"] == "➡️ без изменений")

                c1, c2, c3 = st.columns(3)
                c1.metric("Улучшилось", improved, delta=f"+{improved}", delta_color="normal")
                c2.metric("Ухудшилось", worsened, delta=f"-{worsened}" if worsened else "0", delta_color="inverse")
                c3.metric("Без изменений", unchanged)

                st.dataframe(cmp_df, width='stretch', hide_index=True)

    with tab5:
        render_logs_table(df)

    # --- Export ---
    st.divider()
    st.subheader("📦 Экспорт отчета")

    client_name = st.text_input(
        "Название клиента / Проекта",
        value="DeepThroath User",
        help="Отображается на обложке отчета",
    )

    col_pdf, col_md = st.columns(2)

    with col_pdf:
        if st.button("📄 Сгенерировать PDF-отчет"):
            with st.spinner("Создание профессионального отчета..."):
                try:
                    ctx = build_report_context(df, history_df, client_name=client_name)
                    html = render_html_report(ctx)
                    pdf_bytes = export_pdf(html)
                    st.download_button(
                        label="⬇️ Скачать PDF",
                        data=pdf_bytes,
                        file_name=f"DeepThroath_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                    )
                    st.success("✅ Отчет успешно сформирован!")
                except (OSError, RuntimeError):
                    st.error("❌ PDF недоступен: не установлены системные библиотеки Pango.")
                    st.code("brew install pango gdk-pixbuf libffi", language="bash")
                    st.info("После установки перезапустите дашборд. Пока используйте Markdown-экспорт.")
                except Exception as e:
                    st.error(f"❌ Непредвиденная ошибка: {e}")

    with col_md:
        if st.button("📝 Сгенерировать Markdown-отчет"):
            with st.spinner("Создание Markdown-отчета..."):
                ctx = build_report_context(df, history_df, client_name=client_name)
                md = render_markdown_report(ctx)
                st.download_button(
                    label="⬇️ Скачать Markdown",
                    data=md.encode("utf-8-sig"),
                    file_name=f"DeepThroath_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                    mime="text/markdown; charset=utf-8",
                )
                st.success("✅ Markdown-отчет готов!")


# ══════════════════════════════════════════════════════════════════════════════
# РАЗДЕЛ: КАЧЕСТВО RAG
# ══════════════════════════════════════════════════════════════════════════════

elif section == "✅ Качество RAG":
    st.header("Анализ качества RAG")

    if not has_quality:
        st.warning(
            "Результаты оценки не найдены. Сначала запустите оценку:\n"
            "```bash\npython eval/scripts/run_eval.py --input <путь_к_данным.json>\n```"
        )
        st.stop()

    # Run selector
    eval_df = latest_eval_df  # default
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

    # --- Tabs ---
    qtab1, qtab2, qtab3, qtab4 = st.tabs(["Обзор", "По категориям", "Детали записей", "Тренд"])

    with qtab1:
        ar_scores = eval_df["answer_relevancy_score"].dropna() if "answer_relevancy_score" in eval_df.columns else pd.Series(dtype=float)
        fa_scores = eval_df["faithfulness_score"].dropna() if "faithfulness_score" in eval_df.columns else pd.Series(dtype=float)
        ar_passed = eval_df["answer_relevancy_passed"] if "answer_relevancy_passed" in eval_df.columns else pd.Series(dtype=bool)

        ar_mean = float(ar_scores.mean()) if not ar_scores.empty else 0.0
        fa_mean = float(fa_scores.mean()) if not fa_scores.empty else None
        pass_rate_val = float(ar_passed.mean()) if not ar_passed.empty else 0.0
        total_records = len(eval_df)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AR Score (среднее)", f"{ar_mean:.3f}", help="Средний Answer Relevancy Score")
        c2.metric(
            "Faithfulness Score",
            f"{fa_mean:.3f}" if fa_mean is not None else "—",
            help="Средний Faithfulness Score (только записи с контекстом)",
        )
        c3.metric("Pass Rate", f"{pass_rate_val:.1%}", help="Доля записей с AR >= порога")
        c4.metric("Записей", total_records, help="Всего записей в прогоне")

        st.divider()

        col_ar, col_fa = st.columns(2)
        with col_ar:
            st.plotly_chart(ar_by_category_bar(eval_df), width="stretch")
        with col_fa:
            if not fa_scores.empty:
                st.plotly_chart(faithfulness_vs_relevancy_scatter(eval_df), width="stretch")
            else:
                st.info("Нет данных Faithfulness (поле retrieval_context отсутствует или пусто).")

    with qtab2:
        if "category" not in eval_df.columns:
            st.info("Поле 'category' отсутствует в данных.")
        else:
            categories = sorted(eval_df["category"].dropna().unique())
            for cat in categories:
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

    with qtab3:
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

        # Apply filters
        filtered_eval = eval_df.copy()
        if sel_cats is not None and "category" in filtered_eval.columns:
            filtered_eval = filtered_eval[filtered_eval["category"].isin(sel_cats)]
        if "answer_relevancy_score" in filtered_eval.columns:
            filtered_eval = filtered_eval[
                filtered_eval["answer_relevancy_score"].fillna(0) >= score_threshold
            ]
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

        display_cols_eval = [c for c in ["session_id", "category", "intent", "answer_relevancy_score", "answer_relevancy_passed", "faithfulness_score", "faithfulness_passed"] if c in paged_eval.columns]
        st.dataframe(paged_eval[display_cols_eval], hide_index=True, width="stretch")

        st.subheader("Детали записей")
        for _, row in paged_eval.iterrows():
            ar_val = row.get("answer_relevancy_score")
            ar_passed_val = row.get("answer_relevancy_passed", False)
            icon = "✅" if ar_passed_val else "❌"
            ar_str = f"{ar_val:.3f}" if ar_val is not None else "—"
            cat_label = row.get("category", "—")
            sid = row.get("session_id", "—")
            with st.expander(f"{icon} Session {sid} — {cat_label} | AR={ar_str}"):
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

    with qtab4:
        if eval_runs:
            st.plotly_chart(quality_trend_line(list(reversed(eval_runs))), width="stretch")
        else:
            st.info("Нет данных по нескольким прогонам для отображения тренда.")

    # --- Export ---
    st.divider()
    st.subheader("📦 Экспорт данных качества")

    col_dl_json, col_dl_md = st.columns(2)

    with col_dl_json:
        records_to_export = eval_df.to_dict(orient="records")
        json_bytes = json.dumps(records_to_export, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button(
            label="⬇️ Скачать JSON (все записи)",
            data=json_bytes,
            file_name=f"eval_results_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
        )

    with col_dl_md:
        # Generate inline Markdown report
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
