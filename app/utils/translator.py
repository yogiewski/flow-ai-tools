import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class Translator:
    """Simple translation system for the app."""

    def __init__(self, config_file: str = "config/translations.yml"):
        self.config_file = Path(config_file)
        self.translations: Dict[str, Dict[str, str]] = {}
        self.current_language = "pl"
        self.load_translations()

    def set_language_from_session(self, session_state):
        """Set language from Streamlit session state."""
        if 'language' in session_state:
            self.set_language(session_state.language)
        else:
            session_state.language = self.current_language

    def load_translations(self):
        """Load translations from YAML config file."""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                locales = config.get('locales', {})
                self.translations = locales
        else:
            # Fallback to empty translations if config file doesn't exist
            self.translations = {'en': {}, 'pl': {}}

    def set_language(self, language: str):
        """Set the current language."""
        if language in self.translations:
            self.current_language = language

    def get(self, key: str, default: str = "", lang: Optional[str] = None) -> str:
        """Get translated text for a key."""
        language = lang or self.current_language
        if language in self.translations:
            return self.translations[language].get(key, default)
        return default

    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages with their display names."""
        # Hardcoded display names since the language_selector is bilingual
        return {
            "en": "English",
            "pl": "Polski"
        }

# Global translator instance
translator = Translator()