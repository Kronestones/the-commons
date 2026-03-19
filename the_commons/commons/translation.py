"""
translation.py — The Commons Translation

One tap. Any language. No surveillance attached.

Uses LibreTranslate — free, open source, no API key required
for the public instance. Can be self-hosted for privacy.

Supports translation of posts, comments, and any text.
Language is auto-detected. User chooses target language.

No translation data is stored. No behavioral profile built from
what languages you translate. Private by design.

Codex Law 3: No data selling.
Codex Law 5: Transparency.

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

import httpx
from typing import Optional

# LibreTranslate public instance — free, no key required
# Can be swapped for self-hosted instance for more privacy
LIBRETRANSLATE_URL = "https://libretranslate.com/translate"
DETECT_URL         = "https://libretranslate.com/detect"

# Supported languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
    "ar": "Arabic",
    "hi": "Hindi",
    "ja": "Japanese",
    "ko": "Korean",
    "tr": "Turkish",
    "pl": "Polish",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "fi": "Finnish",
    "no": "Norwegian",
    "uk": "Ukrainian",
    "cs": "Czech",
    "ro": "Romanian",
    "hu": "Hungarian",
    "id": "Indonesian",
    "vi": "Vietnamese",
    "th": "Thai",
    "he": "Hebrew",
    "fa": "Persian",
    "sw": "Swahili",
}


class TranslationManager:

    async def translate(self, text: str,
                        target_language: str,
                        source_language: str = "auto") -> dict:
        """
        Translate text to target language.
        Source language auto-detected if not specified.
        """
        if not text or not text.strip():
            return {"ok": False, "error": "No text to translate."}

        if target_language not in SUPPORTED_LANGUAGES:
            return {"ok": False, "error": f"Language '{target_language}' not supported."}

        if len(text) > 5000:
            return {"ok": False, "error": "Text too long for translation. Maximum 5000 characters."}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    LIBRETRANSLATE_URL,
                    json={
                        "q":      text,
                        "source": source_language,
                        "target": target_language,
                        "format": "text",
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "ok":                True,
                        "translated_text":   data.get("translatedText", ""),
                        "source_language":   source_language,
                        "target_language":   target_language,
                        "target_language_name": SUPPORTED_LANGUAGES.get(target_language, target_language),
                        "note":              "Translation provided by LibreTranslate. No data stored."
                    }
                else:
                    return {"ok": False, "error": "Translation service unavailable. Try again shortly."}

        except httpx.TimeoutException:
            return {"ok": False, "error": "Translation timed out. Try again."}
        except Exception as e:
            return {"ok": False, "error": "Translation unavailable right now."}

    async def detect_language(self, text: str) -> dict:
        """Detect the language of text."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    DETECT_URL,
                    json={"q": text[:500]}  # Only need a sample
                )
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        top = data[0]
                        return {
                            "ok":           True,
                            "language":     top.get("language"),
                            "language_name": SUPPORTED_LANGUAGES.get(
                                top.get("language", ""), "Unknown"
                            ),
                            "confidence":   top.get("confidence", 0),
                        }
                return {"ok": False, "error": "Could not detect language."}
        except Exception:
            return {"ok": False, "error": "Language detection unavailable."}

    def get_supported_languages(self) -> list:
        """Return list of supported languages."""
        return [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ]


translation_manager = TranslationManager()
