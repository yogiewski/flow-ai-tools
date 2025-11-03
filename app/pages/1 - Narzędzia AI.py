import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
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
    page_title=translator.get("prompts_title"),
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
        key="language_selector_ai_tools"
    )

    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        translator.set_language(selected_language)
        st.rerun()

# Initialize repositories
prompts_repo = PromptsRepository()

# Initialize session state
if 'editing_prompt' not in st.session_state:
    st.session_state.editing_prompt = None
if 'show_create_form' not in st.session_state:
    st.session_state.show_create_form = False

def reset_form():
    """Reset the form state."""
    st.session_state.editing_prompt = None
    st.session_state.show_create_form = False

def save_prompt(prompt_data: Dict[str, Any]):
    """Save a prompt and show success message."""
    success = prompts_repo.save_prompt(prompt_data)
    if success:
        st.success(translator.get("status_messages.success"))
        reset_form()
        st.rerun()
    else:
        st.error(translator.get("errors.save_failed"))

def delete_prompt(prompt_id: str):
    """Delete a prompt after confirmation."""
    success = prompts_repo.delete_prompt(prompt_id)
    if success:
        st.success(translator.get("status_messages.success"))
        st.rerun()
    else:
        st.error(translator.get("errors.delete_failed"))

# Main content
st.title(translator.get("prompts_title"))

# Action buttons
if st.button(translator.get("create_new_prompt"), type="secondary", use_container_width=True):
    st.session_state.show_create_form = True
    st.session_state.editing_prompt = None

# Create/Edit Form
if st.session_state.show_create_form or st.session_state.editing_prompt:
    st.header(translator.get("create_new_prompt").replace("⊕ ", ""))

    # Initialize defaults
    default_title = ''
    default_category = 'General'
    default_tags = ''
    default_content = ''

    # Load existing data if editing
    if st.session_state.editing_prompt:
        prompt_data = prompts_repo.get_prompt(st.session_state.editing_prompt)
        if not prompt_data:
            st.error(translator.get("errors.prompt_not_found"))
            reset_form()
        else:
            default_title = prompt_data.get('title', '')
            default_category = prompt_data.get('category', 'General')
            default_tags = ', '.join(prompt_data.get('tags', []))
            default_content = prompt_data.get('content', '')

    with st.form("prompt_form"):
        title = st.text_input(translator.get("prompt_title_label"), value=default_title)
        category_options = [translator.get(f"categories.{cat.lower()}") for cat in ["General", "Sales", "Support", "Technical", "Marketing"]]
        category_keys = ["General", "Sales", "Support", "Technical", "Marketing"]
        category = st.selectbox(
            translator.get("prompt_category_label"),
            category_options,
            index=category_keys.index(default_category)
        )
        # Convert back to English key for storage
        category = category_keys[category_options.index(category)]
        tags_input = st.text_input(translator.get("prompt_tags_label"), value=default_tags)
        content = st.text_area(translator.get("prompt_content_label"), value=default_content, height=300)

        # Preview
        if content:
            st.subheader(translator.get("prompt_preview"))
            st.markdown(content)

        submitted = st.form_submit_button(translator.get("save_prompt_button"))

        if submitted:
            if not title.strip():
                st.error(translator.get("errors.title_required"))
            elif not content.strip():
                st.error(translator.get("errors.content_required"))
            else:
                # Parse tags
                tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

                prompt_data = {
                    'title': title.strip(),
                    'category': category,
                    'tags': tags,
                    'content': content.strip(),
                    'updated_at': datetime.now().isoformat()
                }

                if st.session_state.editing_prompt:
                    prompt_data['id'] = st.session_state.editing_prompt

                save_prompt(prompt_data)

    if st.button(translator.get("cancel_button"), type="secondary"):
        reset_form()
        st.rerun()

else:
    # Prompts List
    prompts = prompts_repo.list_prompts()

    if not prompts:
        st.info(translator.get("no_prompts_found"))
    else:
        for prompt in prompts:
            with st.container():
                col1, col2 = st.columns([3, 2])

                with col1:
                    st.subheader(prompt['title'])
                    if prompt.get('tags'):
                        st.caption(f"{translator.get('tags_label')} {', '.join(prompt['tags'])}")
                    category_translated = translator.get(f"categories.{prompt['category'].lower()}")
                    st.caption(f"{translator.get('category_label')} {category_translated}")

                with col2:
                    # Show first 100 characters of content
                    content_preview = prompts_repo.get_prompt(prompt['id'])
                    if content_preview and content_preview.get('content'):
                        preview = content_preview['content'][:100] + "..." if len(content_preview['content']) > 100 else content_preview['content']
                        st.text(preview)

                    # Action buttons in the description column
                    button_col1, button_col2 = st.columns([1, 1])
                    with button_col1:
                        if st.button(translator.get("edit_button_short"), key=f"edit_{prompt['id']}", type="secondary", use_container_width=True):
                            st.session_state.editing_prompt = prompt['id']
                            st.session_state.show_create_form = False
                            st.rerun()
                    with button_col2:
                        if st.button(translator.get("delete_button_short"), key=f"delete_{prompt['id']}", type="secondary", use_container_width=True):
                            delete_prompt(prompt['id'])

                st.divider()