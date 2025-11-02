import streamlit as st
import time
from typing import List, Dict, Any, Optional
from ..services.llm_factory import get_llm_client
from ..storage.prompts_repo import PromptsRepository
from ..utils.config import get_config
from ..utils.logging import get_logger

logger = get_logger(__name__)

# Page config
st.set_page_config(
    page_title="LLM Chat",
    page_icon="💬",
    layout="wide"
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_prompt' not in st.session_state:
    st.session_state.current_prompt = None
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False

# Load config and repositories
config = get_config()
prompts_repo = PromptsRepository()

def start_chat():
    """Initialize chat with selected prompt."""
    if st.session_state.selected_prompt:
        prompt_data = prompts_repo.get_prompt(st.session_state.selected_prompt)
        if prompt_data:
            st.session_state.current_prompt = prompt_data
            st.session_state.messages = [{"role": "system", "content": prompt_data['content']}]
            st.session_state.chat_started = True
            st.success(f"Chat started with prompt: {prompt_data['title']}")

def clear_chat():
    """Clear the current chat session."""
    st.session_state.messages = []
    st.session_state.current_prompt = None
    st.session_state.chat_started = False

def send_message():
    """Send user message and get LLM response."""
    if not st.session_state.user_input.strip():
        return

    try:
        logger.info(f"Sending message to LLM: {st.session_state.api_flavor} at {st.session_state.base_url}:{st.session_state.port}")

        # Add user message
        user_message = {"role": "user", "content": st.session_state.user_input}
        st.session_state.messages.append(user_message)

        # Get LLM client
        client = get_llm_client(
            st.session_state.api_flavor,
            st.session_state.base_url,
            st.session_state.port
        )

        # Get response
        with st.spinner("Getting response..."):
            response = client.chat(
                st.session_state.messages,
                model=st.session_state.model,
                temperature=st.session_state.temperature,
                max_tokens=st.session_state.max_tokens
            )

        # Add assistant response
        assistant_message = {"role": "assistant", "content": response['content']}
        st.session_state.messages.append(assistant_message)

        # Clear input
        st.session_state.user_input = ""

        logger.info("Message sent and response received successfully")

    except ConnectionError as e:
        error_msg = f"Connection error: Unable to connect to LLM at {st.session_state.base_url}:{st.session_state.port}"
        st.error(error_msg)
        logger.error(f"Connection error: {str(e)}")
    except TimeoutError as e:
        error_msg = "Timeout error: LLM took too long to respond"
        st.error(error_msg)
        logger.error(f"Timeout error: {str(e)}")
    except ValueError as e:
        error_msg = f"Configuration error: {str(e)}"
        st.error(error_msg)
        logger.error(f"Value error: {str(e)}")
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        st.error(error_msg)
        logger.error(f"Unexpected error in send_message: {str(e)}", exc_info=True)

# Sidebar
with st.sidebar:
    st.header("LLM Configuration")

    # LLM Settings
    st.session_state.base_url = st.text_input(
        "Base URL",
        value=config['llm_base_url'],
        help="e.g., http://192.168.1.23"
    )

    st.session_state.port = st.number_input(
        "Port",
        value=config['llm_port'],
        min_value=1,
        max_value=65535
    )

    st.session_state.api_flavor = st.selectbox(
        "API Flavor",
        ["openai-compatible", "ollama", "lmstudio"],
        index=["openai-compatible", "ollama", "lmstudio"].index(config['llm_api_flavor'])
    )

    st.session_state.model = st.text_input(
        "Model",
        value=config['llm_default_model']
    )

    # Prompt Selection
    st.header("Prompt Preset")
    available_prompts = prompts_repo.list_prompts()
    prompt_options = [""] + [p['id'] for p in available_prompts]
    prompt_titles = ["Select a prompt..."] + [p['title'] for p in available_prompts]

    selected_idx = st.selectbox(
        "Choose prompt",
        range(len(prompt_options)),
        format_func=lambda x: prompt_titles[x]
    )

    st.session_state.selected_prompt = prompt_options[selected_idx] if selected_idx > 0 else ""

    if st.button("Start Chat", type="primary"):
        start_chat()

    if st.button("Clear Chat"):
        clear_chat()

    # Advanced Settings
    with st.expander("Advanced Settings"):
        st.session_state.temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=0.7,
            step=0.1
        )

        st.session_state.max_tokens = st.slider(
            "Max Tokens",
            min_value=100,
            max_value=4000,
            value=1000,
            step=100
        )

# Main Chat Interface
st.title("💬 LLM Chat")

if not st.session_state.chat_started:
    st.info("Select a prompt and click 'Start Chat' to begin.")
else:
    # Display current prompt
    if st.session_state.current_prompt:
        st.subheader(f"Using: {st.session_state.current_prompt['title']}")
        with st.expander("View Prompt"):
            st.markdown(st.session_state.current_prompt['content'])

    # Chat messages
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.messages:
            if message["role"] != "system":  # Don't display system messages
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

    # Input
    if prompt := st.chat_input("Type your message...", key="user_input"):
        send_message()
        st.rerun()

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Regenerate Last Response"):
            if len(st.session_state.messages) >= 2:
                # Remove last assistant message and regenerate
                st.session_state.messages.pop()
                send_message()
                st.rerun()

    with col2:
        if st.button("Clear Session"):
            clear_chat()
            st.rerun()