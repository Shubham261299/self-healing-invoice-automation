"""Streamlit dashboard for visualizing automation runs."""
import pandas as pd
import streamlit as st
from pathlib import Path
from src.config import OUTPUT_XLSX, LOGS_DIR

st.set_page_config(page_title="Invoice Bot Dashboard", page_icon="🤖", layout="wide")
st.title("🤖 Self-Healing Invoice Automation — Dashboard")

# --- Top metrics ---
if not OUTPUT_XLSX.exists():
    st.warning("No runs yet. Execute `python main.py` to generate data.")
    st.stop()

df = pd.read_excel(OUTPUT_XLSX)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Runs", len(df))
col2.metric("Successful Logins", int(df["login_ok"].sum()))
col3.metric("Total Heal Events", int(df["heal_count"].sum()))
col4.metric("Last Run", df["timestamp"].iloc[-1] if len(df) else "—")

# --- Charts ---
st.subheader("📈 Heal Events Over Time")
if len(df) > 1:
    chart_df = df.copy()
    chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"])
    st.line_chart(chart_df.set_index("timestamp")[["heal_count", "invoices_found"]])
else:
    st.info("Need at least 2 runs to plot trends.")

# --- Run history ---
st.subheader("📋 Run History")
st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True)

# --- Live logs ---
st.subheader("📜 Latest Log Tail")
log_file = LOGS_DIR / "automation.log"
if log_file.exists():
    lines = log_file.read_text(encoding="utf-8").splitlines()[-50:]
    st.code("\n".join(lines), language="log")
else:
    st.info("No logs yet.")