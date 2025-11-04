import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import requests
import random
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from utils.logging import setup_logging, get_logger
from services.llm_factory import get_llm_client
from storage.prompts_repo import PromptsRepository
from utils.config import get_config
from utils.translator import translator

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Load custom CSS
def load_css():
    css_path = Path(__file__).parent / "ui" / "theme.css"
    if css_path.exists():
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Get random Unsplash photo
@st.cache_data(ttl=300)  # Cache for 5 minutes to allow some variety
def get_random_unsplash_photo():
    """Get a random photo from Unsplash with animals or lighthouses."""
    keywords = ["animal", "wildlife", "lighthouse", "beacon", "light tower"]
    keyword = random.choice(keywords)

    # Add timestamp and random seed to ensure uniqueness
    timestamp = int(time.time())
    random_seed = random.randint(1, 10000)

    try:
        # Try without API key first (Unsplash allows limited requests without key)
        response = requests.get(
            f"https://api.unsplash.com/photos/random?query={keyword}&orientation=landscape&w=1200&h=600&sig={timestamp}&seed={random_seed}",
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "url": data["urls"]["regular"],
                "alt": data["alt_description"] or f"Random {keyword} photo",
                "photographer": data["user"]["name"],
                "photographer_url": data["user"]["links"]["html"]
            }
        else:
            logger.warning(f"Unsplash API returned status {response.status_code}")
    except Exception as e:
        logger.warning(f"Failed to fetch Unsplash photo: {e}")

    # Fallback: Generate a pseudo-random image URL using Lorem Picsum
    # This gives us truly random images without API keys
    image_id = random.randint(1, 1000)
    return {
        "url": f"https://picsum.photos/1200/600?random={image_id}",
        "alt": f"Random landscape photo {image_id}",
        "photographer": "Lorem Picsum",
        "photographer_url": "https://picsum.photos"
    }

# Chat functions
def send_message():
    """Send a message to the LLM with MCP tool orchestration."""
    if not st.session_state.messages:
        return

    try:
        from components.chat_ui import ChatUI
        from services.mcp_client import MCPHTTPClient

        chat_ui = ChatUI()
        mcp_client = MCPHTTPClient()

        # Prepare messages with prompt if selected
        messages_to_send = st.session_state.messages.copy()
        if st.session_state.current_prompt:
            prompt_data = prompts_repo.get_prompt(st.session_state.current_prompt)
            if prompt_data:
                # Add system message with prompt content at the beginning
                system_message = {
                    "role": "system",
                    "content": prompt_data['content']
                }
                messages_to_send.insert(0, system_message)

        # Get available tools
        tools = mcp_client.list_tools()

        # Get user input from the most recent message
        user_input = ""
        for msg in reversed(st.session_state.messages):
            if msg["role"] == "user":
                user_input = msg["content"]
                break

        # Send message with tool orchestration
        st.session_state.messages = chat_ui.send_message(messages_to_send, user_input, tools)

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        error_message = {
            "role": "assistant",
            "content": f"{translator.get('errors.connection_error')}: {str(e)}"
        }
        st.session_state.messages.append(error_message)

def clear_chat():
    """Clear the chat history."""
    st.session_state.messages = []
    st.session_state.chat_started = False

# Set translator language first
if 'language' not in st.session_state:
    st.session_state.language = "pl"
translator.set_language(st.session_state.language)

# Main app entry point
st.set_page_config(
    page_title="FlowAI",
    page_icon="🤖",
    layout="wide"
)

# Load custom styling
load_css()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = None
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

# Initialize services
config = get_config()
prompts_repo = PromptsRepository()

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
        key="language_selector_flowai"
    )

    if selected_language != st.session_state.language:
        st.session_state.language = selected_language
        translator.set_language(selected_language)
        st.rerun()

st.title(f"🤖 {translator.get('app_title')}")
st.markdown(translator.get("app_subtitle"))

# Display random Unsplash photo
photo_data = get_random_unsplash_photo()
st.image(
    photo_data["url"],
    caption=f"Photo by {photo_data['photographer']} on Unsplash",
    use_container_width=True
)

# AI Tool selection
st.markdown("### 🤖 AI Tools")
prompts = prompts_repo.list_prompts()
prompt_options = ["None"] + [p['title'] for p in prompts]
prompt_ids = [None] + [p['id'] for p in prompts]

current_idx = 1 if prompts else 0  # Default to first tool if available
if st.session_state.current_prompt:
    if st.session_state.current_prompt in prompt_ids:
        current_idx = prompt_ids.index(st.session_state.current_prompt)

selected_prompt_idx = st.selectbox(
    translator.get("select_ai_tool"),
    range(len(prompt_options)),
    index=current_idx,
    format_func=lambda x: prompt_options[x],
    key="prompt_selector"
)

selected_prompt_id = prompt_ids[selected_prompt_idx]
st.session_state.current_prompt = selected_prompt_id

# Default Chat Interface
# Chat is always active by default
st.session_state.chat_started = True

# Chat messages
chat_container = st.container()
with chat_container:
    try:
        from components.chat_ui import ChatUI
        from services.mcp_client import MCPHTTPClient

        chat_ui = ChatUI()
        mcp_client = MCPHTTPClient()
        tools = mcp_client.list_tools()

        # Filter out system messages for display
        display_messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]
        chat_ui.render_chat(display_messages, tools)
    except ImportError:
        # Fallback to simple display if imports fail
        for message in st.session_state.messages:
            if message["role"] != "system":  # Don't display system messages
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

# Enhanced input styling - monochrome
st.markdown("""
<style>
.stChatInput {
    border: 2px solid #555555 !important;
    border-radius: 8px !important;
    background: #F5F5F5 !important;
}
.stChatInput:focus-within {
    border-color: #333333 !important;
    box-shadow: 0 0 0 3px rgba(85, 85, 85, 0.1) !important;
}
</style>
""", unsafe_allow_html=True)

# Input
if prompt := st.chat_input(translator.get("status_messages.sending"), key="home_user_input"):
    # Add user message
    user_message = {
        "role": "user",
        "content": prompt
    }
    st.session_state.messages.append(user_message)
    send_message()
    st.rerun()

# Action buttons
col1, col2 = st.columns(2)
with col1:
    if st.button(translator.get("clear_session_button"), type="secondary"):
        clear_chat()
        st.rerun()