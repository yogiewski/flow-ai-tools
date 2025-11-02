import streamlit as st
from pathlib import Path
from .utils.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Load custom CSS
def load_css():
    css_path = Path(__file__).parent / "ui" / "theme.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main app entry point for multi-page Streamlit app
st.set_page_config(
    page_title="Flow AI Chat",
    page_icon="🤖",
    layout="wide"
)

# Load custom styling
load_css()

st.title("🤖 Flow AI Chat")
st.markdown("Internal sales team LLM chat application")

st.markdown("""
Navigate using the sidebar to:
- **Chat**: Start conversations with your configured LLM
- **Prompts Manager**: Create and manage prompt presets
- **Settings**: Configure LLM connections and defaults
""")

# This file serves as the home page when no specific page is selected