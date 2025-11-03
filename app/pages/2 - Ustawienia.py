import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from pathlib import Path
from utils.config import get_config
from utils.translator import translator
import shutil

# Load custom CSS
def load_css():
    css_path = Path(__file__).parent.parent / "ui" / "theme.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Page config
st.set_page_config(
    page_title=translator.get("nav_settings"),
    page_icon="⚙",
    layout="wide"
)

# Load custom styling
load_css()

# Set translator language
if 'language' not in st.session_state:
    st.session_state.language = "pl"
translator.set_language(st.session_state.language)

def apply_theme(theme_name: str):
    """Apply a theme by copying the theme file to config.toml."""
    themes_dir = Path('.streamlit/themes')
    theme_file = themes_dir / f"{theme_name}.toml"
    config_file = Path('.streamlit/config.toml')

    if theme_file.exists():
        shutil.copy(theme_file, config_file)
        st.success(f"{translator.get('status_messages.success')}: {theme_name.replace('_', ' ').title()} {translator.get('theme_applied')}")
        st.info(translator.get("settings_instructions"))
    else:
        st.error(translator.get("theme_not_found").format(theme_name=theme_name))

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

    st.success(translator.get("status_messages.success"))

# Load current config
config = get_config()

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
        key="language_selector_settings"
    )

    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        translator.set_language(selected_language)
        st.rerun()

st.title(translator.get("settings_title"))

st.header(translator.get("llm_settings_title"))

# LLM Settings Form
with st.form("llm_settings"):

    base_url = st.text_input(
        translator.get("base_url_label"),
        value=config['llm_base_url'],
        help=translator.get("base_url_help")
    )

    port = st.number_input(
        translator.get("port_label"),
        value=config['llm_port'],
        min_value=1,
        max_value=65535,
        help=translator.get("base_url_help")
    )

    api_flavors = translator.get("api_flavors")
    api_options = list(api_flavors.keys())
    api_labels = [api_flavors[flavor] for flavor in api_options]

    selected_api_idx = api_options.index(config['llm_api_flavor']) if config['llm_api_flavor'] in api_options else 0
    api_flavor = st.selectbox(
        translator.get("api_flavor_label"),
        api_options,
        index=selected_api_idx,
        format_func=lambda x: api_flavors[x],
        help=translator.get("api_flavor_label")
    )

    default_model = st.text_input(
        translator.get("model_label"),
        value=config['llm_default_model'],
        help=translator.get("model_label")
    )

    st.header(translator.get("flowhub_settings_title"))

    flowhub_enabled = st.checkbox(
        translator.get("flowhub_enabled_label"),
        value=config['flowhub_hooks_enabled'],
        help=translator.get("flowhub_enabled_help")
    )

    flowhub_url = st.text_input(
        translator.get("flowhub_url_label"),
        value=config['flowhub_webhook_url'],
        help=translator.get("flowhub_url_help"),
        disabled=not flowhub_enabled
    )

    submitted = st.form_submit_button(translator.get("save_settings_button"))

# Theme Selection (outside the form)
st.header(translator.get("ui_theme_title"))

st.info(translator.get("using_minimal_theme"))

if st.button(translator.get("reset_theme_button"), type="secondary"):
    apply_theme("minimal")

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
st.header(translator.get("current_config_title"))

st.subheader(translator.get("env_vars_title"))
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
        st.caption(f"{key}: {translator.get('not_set')}")
    else:
        st.caption(f"{key}: {value}")

# File locations
st.header(translator.get("file_locations_title"))
st.caption(f"{translator.get('settings_file_caption')} {Path('.env.local').absolute()}")
st.caption(f"{translator.get('prompts_directory_caption')} {Path('data/prompts').absolute()}")

# Instructions
st.header(translator.get("instructions_title"))
st.markdown(translator.get("settings_instructions"))

# Test Connection (optional)
st.header(translator.get("test_connection_button"))
if st.button(translator.get("test_connection_button")):
    try:
        from services.llm_factory import get_llm_client

        client = get_llm_client(
            config['llm_api_flavor'],
            config['llm_base_url'],
            config['llm_port']
        )

        models = client.models()
        st.success(f"{translator.get('connection_success')}! {translator.get('available_models')}: {', '.join(models[:5])}")

    except Exception as e:
        st.error(f"{translator.get('connection_failed')}: {str(e)}")