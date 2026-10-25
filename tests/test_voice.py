"""
Unit and integration tests for ResQAI Voice Assistance Subsystem.
Validates BCP-47 speech locales, speech synthesis text cleaning,
and localized voice instruction prompts.
"""

from app.services.voice_service import (
    get_speech_locale,
    prepare_text_for_speech,
    get_voice_guidance_prompt,
    get_speech_config
)

def test_speech_locale_mappings():
    assert get_speech_locale('en') == 'en-US'
    assert get_speech_locale('hi') == 'hi-IN'
    assert get_speech_locale('mr') == 'mr-IN'
    assert get_speech_locale('ur') == 'ur-PK'
    assert get_speech_locale('es') == 'es-ES'
    assert get_speech_locale('ar') == 'ar-SA'
    # Fallback for unknown
    assert get_speech_locale('xyz') == 'en-US'

def test_prepare_text_for_speech_markdown_cleaning():
    raw_markdown = """
    **CRITICAL WARNING**:
    * Move to higher ground immediately!
    * Do not walk through moving water.
    * For emergency rescue, [Click Here](https://resqai.org) or dial 112.
    """
    cleaned = prepare_text_for_speech(raw_markdown)
    assert "**" not in cleaned
    assert "[" not in cleaned
    assert "https://" not in cleaned
    assert "Move to higher ground immediately" in cleaned
    assert "CRITICAL WARNING" in cleaned

def test_voice_guidance_prompts():
    en_prompt = get_voice_guidance_prompt('en')
    hi_prompt = get_voice_guidance_prompt('hi')
    assert "describe your emergency" in en_prompt.lower()
    assert "आपातकालीन" in hi_prompt

def test_speech_config_payload():
    config = get_speech_config('hi')
    assert config['locale'] == 'hi-IN'
    assert 'आपातकालीन' in config['prompt']
    assert config['rate'] == 1.0
