"""
Unit and integration tests for ResQAI AI Triage and Decision Engine.
Tests pluggable provider architecture, rule-based deterministic fallback,
multilingual intent classification, and emergency urgency scoring.
"""

from app.services.ai_service import classify_and_triage, get_ai_emergency_response, AIService
from app.services.classification_rules import classify_message_rule_based, get_safety_instructions

def test_ai_triage_critical_fire_detection():
    text = "Thick smoke and fire trapped on the 4th floor, people cannot breathe"
    triage = classify_and_triage(text, language='en')
    assert triage['category'] in ['fire', 'Fire Outbreak']
    assert triage['urgency'] in ['Critical', 'High']
    assert triage['is_high_risk'] is True

def test_ai_triage_multilingual_hindi():
    text = "इमारत में भीषण आग लग गई है, तुरंत मदद चाहिए"
    triage = classify_and_triage(text, language='hi')
    assert triage['category'] in ['fire', 'Fire Outbreak']
    assert triage['urgency'] in ['Critical', 'High']

def test_ai_triage_multilingual_marathi_flood():
    text = "नदीचे पाणी घरात शिरले आहे, पूर आला आहे आम्ही छतावर अडकलो आहोत"
    triage = classify_and_triage(text, language='mr')
    assert triage['category'] in ['flood', 'Flood / Waterlogging']
    assert triage['urgency'] in ['Critical', 'High', 'Medium']

def test_ai_triage_multilingual_urdu_earthquake():
    text = "زلزلے کے شدید جھٹکے، دیواریں گر گئی ہیں"
    triage = classify_and_triage(text, language='ur')
    assert triage['category'] in ['earthquake', 'Earthquake']

def test_ai_triage_medical_cardiac_arrest():
    text = "Elderly person collapsed unconscious, not breathing, cardiac arrest CPR"
    triage = classify_and_triage(text, language='en')
    assert triage['category'] in ['medical', 'Medical Emergency']
    assert triage['urgency'] in ['Critical', 'High']

def test_ai_chat_response_fallback_mode_without_api_key():
    ai = AIService(api_key=None)
    response = ai.generate_emergency_advice("There is an electrical fire near my gas cylinder", language='en')
    assert response is not None
    assert 'reply' in response
    assert response['is_fallback'] is True
    assert '112' in response['reply'] or '101' in response['reply']
    assert response['urgency'] in ['Critical', 'High']

def test_unknown_query_graceful_handling():
    text = "What is the weather like tomorrow morning?"
    triage = classify_message_rule_based(text)
    assert triage['category'] == 'other'
    instructions = get_safety_instructions('other', language='en')
    assert '112' in instructions
