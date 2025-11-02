import streamlit as st
import os
from pathlib import Path
from ..utils.config import get_config

# Page config
st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
    layout="wide"
)

def save_settings(settings: dict):
    """Save settings to .env.local file."""
    env_local_path = Path('.env.local')

    # Read existing content
    existing_content = {}
    if env_local_path.exists():
        with open(env_local_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        existing_content[key] = value

    # Update with new settings
    existing_content.update({
        'LLM_BASE_URL': settings['base_url'],
        'LLM_PORT': str(settings['port']),
        'LLM_API_FLAVOR': settings['api_flavor'],
        'LLM_DEFAULT_MODEL': settings['default_model'],
        'FLOWHUB_HOOKS_ENABLED': 'true' if settings['flowhub_enabled'] else 'false',
        'FLOWHUB_WEBHOOK_URL': settings['flowhub_url']
    })

    # Write back to file
    with open(env_local_path, 'w') as f:
        f.write("# Local environment overrides\n")
        f.write("# This file is loaded after .env and overrides those values\n\n")
        for key, value in existing_content.items():
            f.write(f"{key}={value}\n")

    st.success("Settings saved! Please restart the app for changes to take effect.")

# Load current config
config = get_config()

st.title("⚙️ Settings")

st.header("LLM Configuration")

# LLM Settings Form
with st.form("llm_settings"):
    st.subheader("Default LLM Settings")

    base_url = st.text_input(
        "Base URL",
        value=config['llm_base_url'],
        help="Default base URL for LLM API"
    )

    port = st.number_input(
        "Port",
        value=config['llm_port'],
        min_value=1,
        max_value=65535,
        help="Default port for LLM API"
    )

    api_flavor = st.selectbox(
        "API Flavor",
        ["openai-compatible", "ollama", "lmstudio"],
        index=["openai-compatible", "ollama", "lmstudio"].index(config['llm_api_flavor']),
        help="Type of LLM API to use"
    )

    default_model = st.text_input(
        "Default Model",
        value=config['llm_default_model'],
        help="Default model name to use"
    )

    st.header("FlowHub Integration")

    flowhub_enabled = st.checkbox(
        "Enable FlowHub Hooks",
        value=config['flowhub_hooks_enabled'],
        help="Send events to FlowHub for integration with other systems"
    )

    flowhub_url = st.text_input(
        "FlowHub Webhook URL",
        value=config['flowhub_webhook_url'],
        help="URL to send webhook events to FlowHub",
        disabled=not flowhub_enabled
    )

    submitted = st.form_submit_button("Save Settings")

    if submitted:
        settings = {
            'base_url': base_url,
            'port': port,
            'api_flavor': api_flavor,
            'default_model': default_model,
            'flowhub_enabled': flowhub_enabled,
            'flowhub_url': flowhub_url
        }
        save_settings(settings)

# Current Configuration Display
st.header("Current Configuration")

st.subheader("Environment Variables")
env_vars = {
    'LLM_BASE_URL': config['llm_base_url'],
    'LLM_PORT': config['llm_port'],
    'LLM_API_FLAVOR': config['llm_api_flavor'],
    'LLM_DEFAULT_MODEL': config['llm_default_model'],
    'FLOWHUB_HOOKS_ENABLED': config['flowhub_hooks_enabled'],
    'FLOWHUB_WEBHOOK_URL': config['flowhub_webhook_url']
}

for key, value in env_vars.items():
    if key == 'FLOWHUB_WEBHOOK_URL' and not value:
        st.caption(f"{key}: (not set)")
    else:
        st.caption(f"{key}: {value}")

# File locations
st.header("File Locations")
st.caption(f"Settings file: {Path('.env.local').absolute()}")
st.caption(f"Prompts directory: {Path('data/prompts').absolute()}")

# Instructions
st.header("Instructions")
st.markdown("""
**To apply settings changes:**
1. Save the settings above
2. Restart the Streamlit app
3. The new defaults will be loaded

**Note:** Settings are stored in `.env.local` which overrides `.env` values.
""")

# Test Connection (optional)
st.header("Test Connection")
if st.button("Test LLM Connection"):
    try:
        from ..services.llm_client import get_llm_client

        client = get_llm_client(
            config['llm_api_flavor'],
            config['llm_base_url'],
            config['llm_port']
        )

        models = client.models()
        st.success(f"Connection successful! Available models: {', '.join(models[:5])}")

    except Exception as e:
        st.error(f"Connection failed: {str(e)}")