import streamlit as st

st.set_page_config(page_title="Funding Arb Engine", layout="wide")
st.title("Hyperliquid Funding Arb Engine")
st.caption("Realtime dashboard placeholder. Wire this to FastAPI/Redis before live operation.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Engine", "Paused")
col2.metric("Exposure", "0.0%")
col3.metric("Open Positions", "0")
col4.metric("Daily PnL", "$0.00")
