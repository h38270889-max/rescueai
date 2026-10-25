"""
ResQAI Voice Assistance Service.
Provides speech recognition locale configurations, text normalization for speech synthesis,
and multilingual speech profiles for hands-free emergency communication.
"""

import re

# BCP-47 locale mapping for Web Speech Recognition and Speech Synthesis
SPEECH_LOCALES = {
    'en': 'en-US',
    'hi': 'hi-IN',
    'mr': 'mr-IN',
    'ur': 'ur-PK',
    'bn': 'bn-IN',
    'ta': 'ta-IN',
    'te': 'te-IN',
    'gu': 'gu-IN',
    'kn': 'kn-IN',
    'ml': 'ml-IN',
    'pa': 'pa-IN',
    'es': 'es-ES',
    'ar': 'ar-SA',
    'fr': 'fr-FR'
}

VOICE_PROMPTS = {
    'en': "Please describe your emergency clearly: your location, what happened, and if anyone is injured.",
    'hi': "कृपया अपनी आपातकालीन स्थिति स्पष्ट रूप से बताएं: आपका स्थान, क्या हुआ, और क्या कोई घायल है।",
    'mr': "कृपया तुमची आणीबाणी स्पष्टपणे सांगा: तुमचे ठिकाण, काय घडले आणि कोणी जखमी आहे का.",
    'ur': "براہ کرم اپنی ہنگامی صورتحال واضح طور پر بیان کریں: آپ کا مقام، کیا ہوا، اور کیا کوئی زخمی ہے۔",
    'es': "Por favor describa su emergencia claramente: su ubicación, qué ocurrió y si hay heridos.",
    'ar': "يرجى وصف حالة الطوارئ الخاصة بك بوضوح: موقعك، وما حدث، وما إذا كان هناك أي مصابين.",
    'fr': "Veuillez décrire clairement votre urgence : votre position, ce qui s'est passé et s'il y a des blessés."
}


def get_speech_locale(lang_code):
    """Return BCP-47 locale string for browser speech recognition/synthesis."""
    return SPEECH_LOCALES.get(lang_code, 'en-US')


def prepare_text_for_speech(text):
    """
    Clean markdown formatting, URLs, bullet symbols, and excessive whitespace
    so that browser speech synthesis produces natural, fluent vocal instructions.
    """
    if not text:
        return ""

    # Remove markdown links [text](url) -> text
    cleaned = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)
    # Remove bold, italics, code delimiters
    cleaned = re.sub(r'[*_`#~]', '', cleaned)
    # Remove HTML tags if present
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    # Convert bullet points into slight pauses / commas
    cleaned = re.sub(r'^\s*[-•*]\s+', ', ', cleaned, flags=re.MULTILINE)
    # Normalize multiple newlines/spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def get_voice_guidance_prompt(lang_code):
    """Return localized spoken instruction prompt for speech-to-text activation."""
    return VOICE_PROMPTS.get(lang_code, VOICE_PROMPTS['en'])


def get_speech_config(lang_code='en'):
    """Generate client-side configuration payload for Web Speech API."""
    return {
        'locale': get_speech_locale(lang_code),
        'prompt': get_voice_guidance_prompt(lang_code),
        'rate': 1.0,
        'pitch': 1.0,
        'continuous': False,
        'interim_results': True
    }
