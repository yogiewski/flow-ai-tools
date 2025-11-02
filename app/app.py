import streamlit as st

st.set_page_config(
    page_title="FlowAI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 FlowAI")
st.markdown("Welcome to FlowAI - your AI assistant platform")

st.markdown("---")

# Auto-redirect to FlowAI page
st.markdown("Loading FlowAI...")
st.switch_page("pages/1_FlowAI.py")
