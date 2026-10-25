"""
ResQAI Multilingual Translation and Language Detection Service.
Provides UI internationalization for 14 languages, unicode script detection,
and AI-assisted or fallback translation for emergency incident descriptions.
"""

import os
import json
import logging
from flask import current_app
from app.services.ai_service import get_gemini_client

logger = logging.getLogger(__name__)

# Cached dictionary of loaded translation catalogs
_TRANSLATION_CACHE = {}

# Unicode script ranges for zero-dependency local language detection
SCRIPT_RANGES = [
    ((0x0900, 0x097F), 'hi'),  # Devanagari (Hindi / Marathi)
    ((0x0980, 0x09FF), 'bn'),  # Bengali
    ((0x0A00, 0x0A7F), 'pa'),  # Gurmukhi (Punjabi)
    ((0x0A80, 0x0AFF), 'gu'),  # Gujarati
    ((0x0B80, 0x0BFF), 'ta'),  # Tamil
    ((0x0C00, 0x0C7F), 'te'),  # Telugu
    ((0x0C80, 0x0CFF), 'kn'),  # Kannada
    ((0x0D00, 0x0D7F), 'ml'),  # Malayalam
    ((0x0600, 0x06FF), 'ar'),  # Arabic / Urdu
]

def detect_language(text):
    """
    Detect probable language of emergency text using unicode script analysis.
    Returns (lang_code, confidence).
    """
    if not text or not text.strip():
        return ('en', 0.5)

    script_counts = {}
    total_letters = 0

    for char in text:
        cp = ord(char)
        if char.isalpha():
            total_letters += 1
            for (start, end), lang in SCRIPT_RANGES:
                if start <= cp <= end:
                    script_counts[lang] = script_counts.get(lang, 0) + 1
                    break

    if not total_letters or not script_counts:
        # Check Spanish / French specific diacritics
        lower = text.lower()
        if any(c in lower for c in '¿¡áéíóúñ'):
            return ('es', 0.85)
        if any(c in lower for c in 'àâçèéêëîïôùû'):
            return ('fr', 0.85)
        return ('en', 0.8)

    top_lang = max(script_counts, key=script_counts.get)
    ratio = script_counts[top_lang] / total_letters
    
    # If devanagari, check if marathi markers are present
    if top_lang == 'hi':
        marathi_words = ['आहे', 'आहोत', 'नाही', 'मदत', 'झाली', 'पाहिजे', 'झाला']
        if any(w in text for w in marathi_words):
            return ('mr', min(0.95, 0.70 + ratio * 0.25))

    # If arabic script, check if urdu markers are present
    if top_lang == 'ar':
        urdu_chars = ['ٹ', 'ڈ', 'ڑ', 'ں', 'ے', 'ہ', 'ھ']
        if any(c in text for c in urdu_chars):
            return ('ur', min(0.95, 0.70 + ratio * 0.25))

    return (top_lang, min(0.95, 0.65 + ratio * 0.3))


def detect_script_language(text):
    """Convenience helper returning just the detected language code."""
    lang, _ = detect_language(text)
    return lang


def is_rtl_language(lang_code):
    """Return True if language is written Right-to-Left (e.g. Urdu, Arabic)."""
    return lang_code in ('ur', 'ar')


def get_translation_string(key, lang='en', default=None):
    """Convenience helper to fetch a translated UI string."""
    return translate_ui(key, lang_code=lang, default=default)


# 14 Supported Languages dictionary
SUPPORTED_LANGUAGES = {
    'en': {'name': 'English', 'native': 'English', 'dir': 'ltr'},
    'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'dir': 'ltr'},
    'mr': {'name': 'Marathi', 'native': 'मराठी', 'dir': 'ltr'},
    'ur': {'name': 'Urdu', 'native': 'اردو', 'dir': 'rtl'},
    'bn': {'name': 'Bengali', 'native': 'বাংলা', 'dir': 'ltr'},
    'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'dir': 'ltr'},
    'te': {'name': 'Telugu', 'native': 'తెలుగు', 'dir': 'ltr'},
    'gu': {'name': 'Gujarati', 'native': 'ગુજરાતી', 'dir': 'ltr'},
    'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'dir': 'ltr'},
    'ml': {'name': 'Malayalam', 'native': 'മലയാളം', 'dir': 'ltr'},
    'pa': {'name': 'Punjabi', 'native': 'ਪੰਜਾਬੀ', 'dir': 'ltr'},
    'es': {'name': 'Spanish', 'native': 'Español', 'dir': 'ltr'},
    'ar': {'name': 'Arabic', 'native': 'العربية', 'dir': 'rtl'},
    'fr': {'name': 'French', 'native': 'Français', 'dir': 'ltr'}
}



def load_translations(lang_code):
    """Load translation JSON file for the given language code."""
    if lang_code in _TRANSLATION_CACHE:
        return _TRANSLATION_CACHE[lang_code]

    base_dir = current_app.root_path if current_app else os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, 'translations', f"{lang_code}.json")

    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _TRANSLATION_CACHE[lang_code] = data
                return data
        except Exception as e:
            logger.error(f"Error loading translation file {file_path}: {e}")

    # Fallback to English
    if lang_code != 'en':
        return load_translations('en')
    return {}


def translate_ui(key, lang_code='en', default=None):
    """Translate a UI string key into the target language."""
    catalog = load_translations(lang_code)
    if key in catalog:
        return catalog[key]
    
    # Fallback to English catalog
    en_catalog = load_translations('en')
    return en_catalog.get(key, default or key)


def translate_emergency_message(text, source_lang, target_lang='en'):
    """
    Translate an emergency incident description so responders can understand it.
    Always preserves original text.
    """
    if not text or not text.strip():
        return {
            'original_text': text,
            'translated_text': text,
            'confidence': 1.0,
            'service': 'none',
            'warning': None
        }

    if source_lang == target_lang:
        return {
            'original_text': text,
            'translated_text': text,
            'confidence': 1.0,
            'service': 'none',
            'warning': None
        }

    client = get_gemini_client()
    if client:
        try:
            prompt = (
                f"Translate the following emergency report description from language code '{source_lang}' "
                f"to '{target_lang}'. Maintain medical and urgency accuracy. "
                f"Output ONLY the translated text without commentary:\n\n{text}"
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            translated = response.text.strip()
            return {
                'original_text': text,
                'translated_text': translated,
                'confidence': 0.92,
                'service': 'gemini',
                'warning': None
            }
        except Exception as e:
            logger.info(f"AI translation failed, using fallback notice: {e}")

    # Graceful fallback: when external translation API is unavailable,
    # preserve the exact message with an honest explanatory warning.
    return {
        'original_text': text,
        'translated_text': f"[Original {source_lang.upper()}]: {text}",
        'confidence': 0.50,
        'service': 'fallback_preserved',
        'warning': "Automated translation API currently offline or not configured. Original message displayed in full to avoid inaccurate triage."
    }
