import streamlit as st
from typing import List, Dict, Any
from utils.translator import translator

def display_message_bubble(message: Dict[str, Any]):
    """Display a chat message in a styled bubble."""
    role = message.get("role", "user")
    content = message.get("content", "")

    if role == "user":
        st.markdown(f"""
        <div style="
            background-color: #e3f2fd;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #2196f3;
        ">
        <strong>You:</strong><br>{content}
        </div>
        """, unsafe_allow_html=True)
    elif role == "assistant":
        st.markdown(f"""
        <div style="
            background-color: #f5f5f5;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #4caf50;
        ">
        <strong>Assistant:</strong><br>{content}
        </div>
        """, unsafe_allow_html=True)
    elif role == "system":
        st.markdown(f"""
        <div style="
            background-color: #fff3e0;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
            border-left: 4px solid #ff9800;
            font-style: italic;
        ">
        <strong>System:</strong><br>{content}
        </div>
        """, unsafe_allow_html=True)

def prompt_card(prompt: Dict[str, str], on_select=None, on_edit=None, on_delete=None):
    """Display a prompt as a card with action buttons."""
    with st.container():
        st.subheader(f"📝 {prompt['title']}")
        categories = translator.get("categories")
        category_display = categories.get(prompt.get('category', 'general'), prompt.get('category', 'General'))
        st.caption(f"{translator.get('prompt_category_label')}: {category_display}")
        if prompt.get('tags'):
            st.caption(f"{translator.get('tags_label')} {', '.join(prompt['tags'])}")

        # Preview content
        content = prompt.get('content', '')
        if len(content) > 150:
            st.text(content[:150] + "...")
        else:
            st.text(content)

        # Action buttons
        col1, col2, col3 = st.columns(3)
        if on_select:
            with col1:
                if st.button(translator.get("select_button"), key=f"select_{prompt['id']}"):
                    on_select(prompt['id'])
        if on_edit:
            with col2:
                if st.button(translator.get("edit_button_short"), key=f"edit_{prompt['id']}"):
                    on_edit(prompt['id'])
        if on_delete:
            with col3:
                if st.button(translator.get("delete_button_short"), key=f"delete_{prompt['id']}", type="secondary"):
                    on_delete(prompt['id'])

        st.divider()

def status_indicator(status: str, message: str):
    """Display a status indicator with icon and message."""
    if status == "success":
        st.success(f"✅ {message}")
    elif status == "error":
        st.error(f"❌ {message}")
    elif status == "warning":
        st.warning(f"⚠️ {message}")
    elif status == "info":
        st.info(f"ℹ️ {message}")
    else:
        st.write(message)

def config_summary(config: Dict[str, Any]):
    """Display a summary of current configuration."""
    st.subheader(translator.get("current_configuration"))

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**{translator.get('llm_settings_section')}**")
        st.caption(f"URL: {config.get('llm_base_url', translator.get('not_set'))}")
        st.caption(f"Port: {config.get('llm_port', translator.get('not_set'))}")
        st.caption(f"Flavor: {config.get('llm_api_flavor', translator.get('not_set'))}")
        st.caption(f"Model: {config.get('llm_default_model', translator.get('not_set'))}")

    with col2:
        st.markdown(f"**{translator.get('integration_section')}**")
        flowhub_status = "Enabled" if config.get('flowhub_hooks_enabled') else "Disabled"
        st.caption(f"{translator.get('flowhub_status')} {flowhub_status}")
        if config.get('flowhub_webhook_url'):
            st.caption(f"{translator.get('webhook_label')} {config['flowhub_webhook_url']}")

def loading_spinner(text: str = "Loading..."):
    """Display a loading spinner."""
    with st.spinner(text):
        return True