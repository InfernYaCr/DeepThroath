import json

import pandas as pd
import streamlit as st

from src.red_team.severity import SEVERITY_BADGE, SEVERITY_ORDER


def render_logs_table(df: pd.DataFrame) -> None:
    st.subheader("Логи атак")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        severity_filter = st.multiselect("Критичность", SEVERITY_ORDER, default=SEVERITY_ORDER)
    with col2:
        vuln_options = sorted(df["vulnerability"].unique().tolist())
        vuln_filter = st.multiselect("Уязвимость", vuln_options, default=vuln_options)
    with col3:
        attack_options = sorted(df["attack_type"].unique().tolist())
        attack_filter = st.multiselect("Тип атаки", attack_options, default=attack_options)
    with col4:
        result_filter = st.radio("Результат", ["Все", "Только взломы", "Только защиты"], index=0)

    filtered = df[
        df["severity"].isin(severity_filter)
        & df["vulnerability"].isin(vuln_filter)
        & df["attack_type"].isin(attack_filter)
    ].copy()

    if result_filter == "Только взломы":
        filtered = filtered[filtered["asr"] > 0]
    elif result_filter == "Только защиты":
        filtered = filtered[filtered["asr"] == 0]

    PAGE_SIZE = 50
    total = len(filtered)
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    page = st.number_input("Страница", min_value=1, max_value=total_pages, value=1, step=1) - 1
    paged = filtered.iloc[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

    st.caption(f"Отображено {page * PAGE_SIZE + 1}–{min((page + 1) * PAGE_SIZE, total)} из {total} записей")

    display_cols = ["severity", "owasp_id", "vulnerability", "attack_type", "pass_rate", "asr", "failed", "total"]
    display_df = paged[display_cols].copy()
    display_df["severity"] = display_df["severity"].map(lambda s: f"{SEVERITY_BADGE.get(s, '')} {s}")
    display_df["pass_rate"] = display_df["pass_rate"].map("{:.1%}".format)
    display_df["asr"] = display_df["asr"].map("{:.1%}".format)

    display_df.columns = [
        "Критичность", "OWASP ID", "Уязвимость", "Метод атаки",
        "Защита (%)", "Взлом (ASR)", "Провалено", "Всего"
    ]
    st.dataframe(display_df, width='stretch', hide_index=True)

    st.subheader("Детали диалогов (доказательная база)")
    if filtered.empty:
        st.info("Нет записей, соответствующих фильтрам.")
        return

    for _, row in filtered.iterrows():
        convs = row.get("conversations", "[]")
        if isinstance(convs, str):
            try:
                convs = json.loads(convs)
            except json.JSONDecodeError:
                convs = []
        if not convs:
            continue

        badge = SEVERITY_BADGE.get(row["severity"], "")
        label = f"{badge} {row['severity']} | {row['vulnerability']} | {row['attack_type']} | ASR: {row['asr']:.1%}"
        with st.expander(label):
            for i, conv in enumerate(convs[:3], 1):
                st.markdown(f"**Диалог {i}**")
                st.markdown(f"**Атака (промпт):** {conv.get('input', 'N/A')}")
                st.markdown(f"**Ответ модели:** {conv.get('output', 'N/A')}")
                verdict = conv.get("score", "N/A")
                color = "red" if verdict == 1 else "green"
                label_text = "ВЗЛОМАНА (ОПАСНО)" if verdict == 1 else "ЗАЩИЩЕНА (БЕЗОПАСНО)"
                st.markdown(f"**Вердикт судьи:** :{color}[{label_text}]")
                st.divider()

    col_csv, col_json = st.columns(2)

    with col_csv:
        csv = filtered.drop(columns=["conversations"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Скачать CSV (без диалогов)", csv, "filtered_logs.csv", "text/csv")

    with col_json:
        records = []
        for _, row in filtered.iterrows():
            convs = row.get("conversations", "[]")
            if isinstance(convs, str):
                try:
                    convs = json.loads(convs)
                except json.JSONDecodeError:
                    convs = []
            records.append({
                "vulnerability": row["vulnerability"],
                "owasp_id": row["owasp_id"],
                "severity": row["severity"],
                "attack_type": row["attack_type"],
                "asr": row["asr"],
                "pass_rate": row["pass_rate"],
                "passed": int(row["passed"]),
                "failed": int(row["failed"]),
                "total": int(row["total"]),
                "model_version": row.get("model_version", ""),
                "judge_version": row.get("judge_version", ""),
                "timestamp": row.get("timestamp", ""),
                "conversations": convs,
            })
        json_bytes = json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8")
        st.download_button("⬇️ Скачать JSON (с диалогами)", json_bytes, "filtered_logs.json", "application/json")
