"""
Unit and integration tests for ResQAI Multilingual Subsystem.
Validates Unicode script detection, 14-language UI translation catalogs,
RTL layout direction detection, and translation preservation.
"""

from app.services.translation_service import (
    detect_script_language,
    get_translation_string,
    translate_emergency_message,
    SUPPORTED_LANGUAGES,
    is_rtl_language
)

def test_detect_script_language():
    assert detect_script_language("नमस्ते, मुझे सहायता चाहिए") == 'hi'
    assert detect_script_language("नमस्कार, मला मदत हवी आहे") == 'mr'
    assert detect_script_language("ہنگامی صورتحال") == 'ur'
    assert detect_script_language("Emergency assistance needed") == 'en'

def test_rtl_language_detection():
    assert is_rtl_language('ur') is True
    assert is_rtl_language('ar') is True
    assert is_rtl_language('en') is False
    assert is_rtl_language('hi') is False
    assert is_rtl_language('mr') is False

def test_all_14_languages_catalogs_load():
    expected_langs = ['en', 'hi', 'mr', 'ur', 'bn', 'ta', 'te', 'gu', 'kn', 'ml', 'pa', 'es', 'ar', 'fr']
    for code in expected_langs:
        assert code in SUPPORTED_LANGUAGES
        string_val = get_translation_string('app_name', lang=code)
        assert string_val is not None and len(string_val) > 0

def test_emergency_message_translation_preserves_original():
    original = "आग लागली आहे कृपया फायर ब्रिगेड पाठवा"
    res = translate_emergency_message(original, source_lang='mr', target_lang='en')
    assert res['original_text'] == original
    assert len(res['translated_text']) > 0
    assert res['confidence'] > 0.0

def test_english_to_english_passthrough():
    original = "Immediate ambulance required for highway accident"
    res = translate_emergency_message(original, source_lang='en', target_lang='en')
    assert res['translated_text'] == original
    assert res['confidence'] == 1.0
