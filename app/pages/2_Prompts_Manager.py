import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional
from ..storage.prompts_repo import PromptsRepository

# Page config
st.set_page_config(
    page_title="Prompts Manager",
    page_icon="📝",
    layout="wide"
)

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
        st.success("Prompt saved successfully!")
        reset_form()
        st.rerun()
    else:
        st.error("Failed to save prompt.")

def delete_prompt(prompt_id: str):
    """Delete a prompt after confirmation."""
    success = prompts_repo.delete_prompt(prompt_id)
    if success:
        st.success("Prompt deleted successfully!")
        st.rerun()
    else:
        st.error("Failed to delete prompt.")

# Main content
st.title("📝 Prompts Manager")

# Action buttons
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("➕ Create New Prompt", type="primary"):
        st.session_state.show_create_form = True
        st.session_state.editing_prompt = None

# Create/Edit Form
if st.session_state.show_create_form or st.session_state.editing_prompt:
    st.header("Create/Edit Prompt")

    # Initialize defaults
    default_title = ''
    default_category = 'General'
    default_tags = ''
    default_content = ''

    # Load existing data if editing
    if st.session_state.editing_prompt:
        prompt_data = prompts_repo.get_prompt(st.session_state.editing_prompt)
        if not prompt_data:
            st.error("Prompt not found.")
            reset_form()
        else:
            default_title = prompt_data.get('title', '')
            default_category = prompt_data.get('category', 'General')
            default_tags = ', '.join(prompt_data.get('tags', []))
            default_content = prompt_data.get('content', '')

    with st.form("prompt_form"):
        title = st.text_input("Title", value=default_title)
        category = st.selectbox(
            "Category",
            ["General", "Sales", "Support", "Technical", "Marketing"],
            index=["General", "Sales", "Support", "Technical", "Marketing"].index(default_category)
        )
        tags_input = st.text_input("Tags (comma-separated)", value=default_tags)
        content = st.text_area("Prompt Content (Markdown)", value=default_content, height=300)

        # Preview
        if content:
            st.subheader("Preview")
            st.markdown(content)

        submitted = st.form_submit_button("Save Prompt")

        if submitted:
            if not title.strip():
                st.error("Title is required.")
            elif not content.strip():
                st.error("Content is required.")
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

    if st.button("Cancel"):
        reset_form()
        st.rerun()

else:
    # Prompts List
    st.header("Available Prompts")

    prompts = prompts_repo.list_prompts()

    if not prompts:
        st.info("No prompts found. Create your first prompt!")
    else:
        for prompt in prompts:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

                with col1:
                    st.subheader(prompt['title'])
                    if prompt.get('tags'):
                        st.caption(f"Tags: {', '.join(prompt['tags'])}")
                    st.caption(f"Category: {prompt['category']}")

                with col2:
                    # Show first 100 characters of content
                    content_preview = prompts_repo.get_prompt(prompt['id'])
                    if content_preview and content_preview.get('content'):
                        preview = content_preview['content'][:100] + "..." if len(content_preview['content']) > 100 else content_preview['content']
                        st.text(preview)

                with col3:
                    if st.button("✏️ Edit", key=f"edit_{prompt['id']}"):
                        st.session_state.editing_prompt = prompt['id']
                        st.session_state.show_create_form = False
                        st.rerun()

                with col4:
                    if st.button("🗑️ Delete", key=f"delete_{prompt['id']}"):
                        delete_prompt(prompt['id'])

                st.divider()