import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import streamlit as st

from src.data.storage import load_history, load_latest, list_scan_files
from src.data.eval_storage import list_eval_runs, load_latest_eval
from src.dashboard.tabs.summary import render_summary
from src.dashboard.tabs.security import render_security
from src.dashboard.tabs.quality import render_quality

st.set_page_config(
    page_title="DeepThroath + Eval — Единый дашборд",
    page_icon="🔬",
    layout="wide",
)

st.title("🔬 DeepThroath + Eval — Единый дашборд безопасности и качества LLM")


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


with st.spinner("Загрузка данных..."):
    sec_df = load_latest()
    history_df = _cached_load_history()
    scan_files = _cached_list_scan_files()
    eval_runs = _cached_list_eval_runs()
    latest_eval_df = _cached_load_latest_eval()

has_security = sec_df is not None
has_quality = latest_eval_df is not None

section = st.sidebar.radio(
    "Раздел",
    ["📊 Сводка", "🔐 Безопасность", "✅ Качество RAG"],
)
st.sidebar.divider()
st.sidebar.caption("DeepThroath + Eval Dashboard")

if section == "📊 Сводка":
    render_summary(sec_df, history_df, scan_files, eval_runs, latest_eval_df)
elif section == "🔐 Безопасность":
    render_security(sec_df, has_security, scan_files, history_df)
elif section == "✅ Качество RAG":
    render_quality(latest_eval_df, has_quality, eval_runs)
