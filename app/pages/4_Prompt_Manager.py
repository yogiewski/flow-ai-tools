import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from storage.prompts_repo import PromptsRepository
from utils.translator import translator

# Load custom CSS
def load_css():
    css_path = Path(__file__).parent.parent / "ui" / "theme.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title="Prompt Manager",
    page_icon="📋",
    layout="wide"
)

# Load custom styling
load_css()

# Set translator language
if 'language' not in st.session_state:
    st.session_state.language = "pl"
translator.set_language(st.session_state.language)

# Language selector in sidebar
with st.sidebar:
    st.markdown(f"### {translator.get('language_selector')}")
    available_languages = translator.get_available_languages()
    language_options = list(available_languages.keys())
    language_labels = [available_languages[lang] for lang in language_options]

    selected_idx = language_options.index(st.session_state.language) if st.session_state.language in language_options else 0
    selected_language = st.selectbox(
        translator.get("select_language"),
        language_options,
        index=selected_idx,
        format_func=lambda x: available_languages[x],
        key="language_selector_prompt_selector"
    )

    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        translator.set_language(selected_language)
        st.rerun()

# Initialize repositories
prompts_repo = PromptsRepository()

# Main content
st.title(f"📋 Prompt Manager")

st.markdown(translator.get("nav_description"))

# Get all prompts
prompts = prompts_repo.list_prompts()

if not prompts:
    st.info(translator.get("no_prompts_found"))
    st.markdown("---")
    if st.button("Create Your First AI Tool", type="secondary"):
        st.switch_page("pages/2_AI_Tools.py")
else:
    st.markdown(f"### Available AI Tools ({len(prompts)})")

    # Display prompts one per line
    for prompt in prompts:
        with st.container():
            # Header with title and actions
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.subheader(f"🛠️ {prompt['title']}")
            with col2:
                if st.button("💬 Use", key=f"use_{prompt['id']}", type="secondary"):
                    st.session_state.current_prompt = prompt['id']
                    st.switch_page("pages/1_FlowAI.py")
            with col3:
                if st.button("✏️ Edit", key=f"edit_{prompt['id']}", type="secondary"):
                    st.switch_page("pages/2_AI_Tools.py")

            # Category and tags
            col1, col2 = st.columns(2)
            with col1:
                category_key = f"categories.{prompt['category'].lower()}"
                st.caption(f"{translator.get('category_label')} {translator.get(category_key)}")
            with col2:
                if prompt.get('tags'):
                    st.caption(f"{translator.get('tags_label')} {', '.join(prompt['tags'])}")

            # Content preview
            if prompt.get('content'):
                content_preview = prompt['content'][:200] + "..." if len(prompt['content']) > 200 else prompt['content']
                st.markdown(f"*{content_preview}*")
            else:
                st.markdown("*No content available*")

            st.divider()

    st.markdown("---")
    st.markdown("### Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Create New AI Tool", type="secondary"):
            st.switch_page("pages/2_AI_Tools.py")
    with col2:
        if st.button("🤖 Start General Chat", type="secondary"):
            st.session_state.current_prompt = None
            st.switch_page("pages/1_FlowAI.py")