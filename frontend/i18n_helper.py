import json
import os
import streamlit as st
from typing import Dict, Any, Optional

class I18nHelper:
    """
    Internationalization helper for Streamlit applications.
    Provides translation functionality with language detection and persistence.
    """

    def __init__(self):
        self.translations: Dict[str, Dict[str, Any]] = {}
        self.current_language = "en"  # Default language
        self.supported_languages = {
            "en": {"name": "English", "flag": "🇺🇸"},
            "pt-BR": {"name": "Português (Brasil)", "flag": "🇧🇷"}
        }
        self.load_translations()
        self.initialize_language()

    def load_translations(self):
        """Load all translation files from the i18n directory."""
        i18n_dir = os.path.join(os.path.dirname(__file__), "i18n")

        for lang_code in self.supported_languages.keys():
            translation_file = os.path.join(i18n_dir, f"{lang_code}.json")

            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
            except FileNotFoundError:
                st.error(f"Translation file not found: {translation_file}")
                # Fallback to empty dict to prevent crashes
                self.translations[lang_code] = {}
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON in translation file {translation_file}: {e}")
                self.translations[lang_code] = {}

    def initialize_language(self):
        """Initialize language based on session state or browser detection."""
        # Check if language is already set in session state
        if "i18n_language" in st.session_state:
            self.current_language = st.session_state.i18n_language
        else:
            # Try to detect browser language
            detected_lang = self.detect_browser_language()
            if detected_lang in self.supported_languages:
                self.current_language = detected_lang
            else:
                self.current_language = "en"  # Fallback to English

            # Save to session state
            st.session_state.i18n_language = self.current_language

    def detect_browser_language(self) -> str:
        """
        Attempt to detect browser language.
        Note: This is limited in Streamlit, but we can try to use query parameters.
        """
        try:
            # Check for language query parameter (e.g., ?lang=pt-BR)
            query_params = st.query_params
            if "lang" in query_params:
                lang = query_params["lang"]
                if lang in self.supported_languages:
                    return lang

            # For now, we'll rely on explicit user selection
            # In a full implementation, you might use JavaScript to detect navigator.language
            return "en"

        except Exception:
            return "en"

    def set_language(self, language_code: str):
        """Set the current language and persist it."""
        if language_code in self.supported_languages:
            self.current_language = language_code
            st.session_state.i18n_language = language_code
            # Trigger a rerun to apply language changes immediately
            st.rerun()

    def get_current_language(self) -> str:
        """Get the current language code."""
        return self.current_language

    def get_language_name(self, language_code: str = None) -> str:
        """Get the display name of a language."""
        lang_code = language_code or self.current_language
        return self.supported_languages.get(lang_code, {}).get("name", lang_code)

    def get_language_flag(self, language_code: str = None) -> str:
        """Get the flag emoji for a language."""
        lang_code = language_code or self.current_language
        return self.supported_languages.get(lang_code, {}).get("flag", "🌐")

    def translate(self, key: str, **kwargs) -> str:
        """
        Translate a key to the current language.

        Args:
            key: Translation key in dot notation (e.g., "navigation.horse_directory")
            **kwargs: Variables to substitute in the translation (e.g., horse_name="Thunder")

        Returns:
            Translated string or the key if translation is not found
        """
        # Get the translation dictionary for current language
        lang_translations = self.translations.get(self.current_language, {})

        # Navigate through nested keys (e.g., "navigation.horse_directory")
        keys = key.split('.')
        value = lang_translations

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # If key not found in current language, try English as fallback
                if self.current_language != "en":
                    en_translations = self.translations.get("en", {})
                    fallback_value = en_translations
                    for fallback_k in keys:
                        if isinstance(fallback_value, dict) and fallback_k in fallback_value:
                            fallback_value = fallback_value[fallback_k]
                        else:
                            # Return the key itself if not found in any language
                            return key
                    value = fallback_value
                else:
                    # Return the key itself if not found
                    return key
                break

        # If value is not a string, return the key
        if not isinstance(value, str):
            return key

        # Substitute variables if provided
        try:
            if kwargs:
                return value.format(**kwargs)
            return value
        except (KeyError, ValueError):
            # If formatting fails, return the original value
            return value

    def language_selector(self, key: str = "language_selector"):
        """
        Create a language selector widget in the sidebar.

        Args:
            key: Unique key for the selectbox widget
        """
        with st.sidebar:
            st.markdown("---")

            # Create options list with flag and name
            language_options = []
            language_mapping = {}

            for lang_code, lang_info in self.supported_languages.items():
                option_text = f"{lang_info['flag']} {lang_info['name']}"
                language_options.append(option_text)
                language_mapping[option_text] = lang_code

            # Find current selection
            current_option = None
            for option, code in language_mapping.items():
                if code == self.current_language:
                    current_option = option
                    break

            # Create selectbox
            selected_option = st.selectbox(
                self.translate("ui.language"),
                options=language_options,
                index=language_options.index(current_option) if current_option else 0,
                key=key
            )

            # Update language if changed
            selected_language = language_mapping[selected_option]
            if selected_language != self.current_language:
                self.set_language(selected_language)

# Global instance for easy import
i18n = I18nHelper()

# Convenience function for translation
def t(key: str, **kwargs) -> str:
    """
    Shorthand function for translation.

    Args:
        key: Translation key in dot notation
        **kwargs: Variables to substitute in the translation

    Returns:
        Translated string
    """
    return i18n.translate(key, **kwargs)