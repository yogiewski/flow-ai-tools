import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env.local', override=True)

def get_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    return {
        'llm_base_url': os.getenv('LLM_BASE_URL', 'http://localhost'),
        'llm_port': int(os.getenv('LLM_PORT', '1234')),
        'llm_api_flavor': os.getenv('LLM_API_FLAVOR', 'openai-compatible'),
        'llm_default_model': os.getenv('LLM_DEFAULT_MODEL', 'gpt-3.5-turbo'),
        'flowhub_hooks_enabled': os.getenv('FLOWHUB_HOOKS_ENABLED', 'false').lower() == 'true',
        'flowhub_webhook_url': os.getenv('FLOWHUB_WEBHOOK_URL', ''),
    }