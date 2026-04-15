import sys
from pathlib import Path

# Ensure project root is on the path when running via `streamlit run`
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime

import pandas as pd
import streamlit as st

from src.data.storage import load_history, load_latest, list_scan_files
from src.dashboard.charts import (
    asr_by_owasp_bar,
    overall_passrate_pie,
    passrate_trend,
    severity_heatmap,
)
from src.dashboard.logs_table import render_logs_table
from src.red_team.severity import get_owasp_category, SEVERITY_BADGE, SEVERITY_ORDER, SEVERITY_COLORS
from src.reports.generator import build_report_context, calculate_security_score
from src.reports.pdf_export import render_html_report, render_markdown_report, export_pdf

st.set_page_config(
    page_title="DeepThroath — Аналитика безопасности LLM",
    page_icon="🔐",
    layout="wide",
)

st.title("🔐 DeepThroath — Аналитика безопасности LLM (Red Teaming)")

@st.cache_data(ttl=60)
def _cached_load_history():
    return load_history()

@st.cache_data(ttl=60)
def _cached_list_scan_files():
    return list_scan_files()

with st.spinner("Загрузка результатов..."):
    latest_df = load_latest()
    history_df = _cached_load_history()

if latest_df is None:
    st.warning(
        "Результаты не найдены. Сначала запустите тестирование:\n"
        "```bash\npython scripts/run_redteam.py\n```"
    )
    st.stop()

# --- Global scan selector ---
scan_files = _cached_list_scan_files()
df = latest_df  # default
if scan_files:
    all_labels = ["📌 Последний скан"] + [s["label"] for s in scan_files]
    sel_idx = st.selectbox(
        "📂 Выбор скана",
        options=range(len(all_labels)),
        format_func=lambda i: all_labels[i],
        key="global_scan",
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

        # Build per-category summary (resolve from registry, take worst ASR per category)
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

    # Attention block
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

    # Sort by ASR then severity
    sorted_df = df.sort_values(["asr", "severity"], ascending=[False, True])

    for _, row in sorted_df.iterrows():
        vuln_name = row["vulnerability"]
        cat = get_owasp_category(vuln_name)
        asr_val = row["asr"]
        badge = SEVERITY_BADGE.get(row["severity"], "⚪")

        # Expander title
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
                data=md.encode("utf-8-sig"),  # BOM for correct encoding detection in editors
                file_name=f"DeepThroath_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown; charset=utf-8",
            )
            st.success("✅ Markdown-отчет готов!")
