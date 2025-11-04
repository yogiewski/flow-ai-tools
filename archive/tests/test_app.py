#!/usr/bin/env python3
"""
Simple test script to verify the app structure and basic functionality.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_imports():
    """Test basic imports work."""
    try:
        from utils.config import get_config
        print("✅ Config import successful")

        config = get_config()
        print(f"✅ Config loaded: {config}")

        from storage.prompts_repo import PromptsRepository
        print("✅ Prompts repo import successful")

        repo = PromptsRepository()
        prompts = repo.list_prompts()
        print(f"✅ Prompts loaded: {len(prompts)} prompts found")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_llm_client():
    """Test LLM client creation."""
    try:
        from services.llm_factory import get_llm_client
        print("✅ LLM factory import successful")

        # Test client creation (won't actually connect)
        client = get_llm_client("openai-compatible", "http://test", 1234)
        print(f"✅ Client created: {type(client).__name__}")

        return True
    except Exception as e:
        print(f"❌ LLM client test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Flow AI Chat App Structure")
    print("=" * 40)

    success = True
    success &= test_imports()
    success &= test_llm_client()

    print("=" * 40)
    if success:
        print("✅ All basic tests passed! The app structure is sound.")
        print("\nTo run the full app:")
        print("1. Use Docker: docker-compose up --build")
        print("2. Or install compatible Python version (3.11-3.13)")
        print("3. Then: pip install -r requirements.txt && streamlit run app/app.py")
    else:
        print("❌ Some tests failed. Check the errors above.")