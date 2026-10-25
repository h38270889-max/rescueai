"""
ResQAI Pluggable AI Service Module.
Integrates official OpenAI Python SDK (and optional Gemini) with seamless,
zero-downtime deterministic fallback for offline, unauthenticated, or network-constrained operations.
"""

import os
import json
import logging
from flask import current_app
from app.services.classification_rules import (
    classify_message_rule_based,
    get_safety_instructions
)

logger = logging.getLogger(__name__)

# System instructions enforcing ethical emergency response boundaries
SYSTEM_EMERGENCY_PROMPT = """You are ResQAI Assistant, an AI Emergency and Disaster Response Triage Assistant.
Your mission is to provide concise, calm, actionable, life-saving instructions during disasters and emergencies.

Strict Operational Guidelines:
1. Prioritize immediate life safety: lead with actionable safety instructions.
2. In all urgent or life-threatening situations, urge the user to dial official emergency services (112 Pan-India / Ambulance 102 / Fire 101 / Police 100).
3. Suggest filing an official ResQAI Emergency Report so human responders can track their location.
4. NEVER diagnose a medical disease or prescribe medications.
5. NEVER fabricate or promise rescue team arrival times, hospital capacities, or dispatch confirmations.
6. Clearly state information when you cannot verify it.
7. Keep responses concise, structured (bullet points), and easy to read on a mobile screen under stress.
8. Respond in the user's preferred language.
"""

def get_openai_client():
    """Attempt to instantiate official OpenAI client if API key is present."""
    api_key = current_app.config.get('OPENAI_API_KEY') if current_app else os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, timeout=10.0)
    except Exception as e:
        logger.warning(f"Failed to initialize OpenAI Client: {e}")
        return None

def get_gemini_client():
    """Attempt to instantiate google-genai client if API key is present."""
    api_key = current_app.config.get('GEMINI_API_KEY') if current_app else os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini Client: {e}")
        return None

def classify_and_triage(text, language='en'):
    """
    Classify an emergency message to extract category, urgency, confidence, and explanation.
    Uses OpenAI (or Gemini) when configured; otherwise uses deterministic rule-based engine.
    """
    # 1. Try OpenAI if configured
    openai_client = get_openai_client()
    if openai_client:
        model_name = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini') if current_app else os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        try:
            prompt = f"""Analyze this emergency message and return ONLY a valid JSON object:
Text: "{text}"
Language: {language}

JSON format required:
{{
  "category": "medical" | "fire" | "flood" | "earthquake" | "road_accident" | "missing_person" | "trapped_person" | "rescue_request" | "shelter_request" | "other",
  "urgency": "Critical" | "High" | "Medium" | "Low",
  "confidence": 0.0 to 1.0,
  "explanation": "Brief 1-sentence reasoning",
  "is_high_risk": true or false
}}
"""
            completion = openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an emergency triage classifier. Output JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw = completion.choices[0].message.content.strip()
            data = json.loads(raw)
            data['is_fallback'] = False
            data['provider'] = 'openai'
            return data
        except Exception as e:
            logger.info(f"OpenAI classification failed, falling back: {e}")

    # 2. Try Gemini fallback if configured
    gemini_client = get_gemini_client()
    if gemini_client:
        try:
            prompt = f"""Analyze this emergency text and return ONLY a valid JSON object:
Text: "{text}"
Language: {language}

JSON format required:
{{
  "category": "medical" | "fire" | "flood" | "earthquake" | "road_accident" | "missing_person" | "trapped_person" | "rescue_request" | "shelter_request" | "other",
  "urgency": "Critical" | "High" | "Medium" | "Low",
  "confidence": 0.0 to 1.0,
  "explanation": "Brief 1-sentence reasoning",
  "is_high_risk": true or false
}}
"""
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config={'temperature': 0.1, 'response_mime_type': 'application/json'}
            )
            data = json.loads(response.text.strip())
            data['is_fallback'] = False
            data['provider'] = 'gemini'
            return data
        except Exception as e:
            logger.info(f"Gemini classification fallback triggered: {e}")

    # 3. Deterministic Local Rule Fallback
    result = classify_message_rule_based(text)
    result['is_fallback'] = True
    result['provider'] = 'rule_based'
    return result

def generate_chat_response(user_message, conversation_history=None, language='en'):
    """
    Generate an emergency assistant reply.
    Combines triage classification with life-saving safety guidance.
    """
    triage = classify_and_triage(user_message, language=language)
    category = triage.get('category', 'other')
    urgency = triage.get('urgency', 'Medium')
    is_fallback = triage.get('is_fallback', True)

    # 1. Try OpenAI if configured
    openai_client = get_openai_client()
    if openai_client:
        model_name = current_app.config.get('OPENAI_MODEL', 'gpt-4o-mini') if current_app else os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
        try:
            messages = [{"role": "system", "content": SYSTEM_EMERGENCY_PROMPT}]
            if conversation_history:
                for msg in conversation_history[-6:]:
                    role = "user" if msg.sender == "user" else "assistant"
                    messages.append({"role": role, "content": msg.message})
            messages.append({"role": "user", "content": f"(Language: {language}) {user_message}"})

            completion = openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.2,
                max_tokens=500
            )
            bot_text = completion.choices[0].message.content.strip()
            
            disclaimer = "\n\n⚠️ *ResQAI provides AI-assisted safety guidance and does not replace official dispatchers. In an immediate life-threatening emergency, dial 112.*"
            if "112" not in bot_text:
                bot_text += disclaimer

            return {
                'response': bot_text,
                'category': category,
                'urgency': urgency,
                'is_fallback': False,
                'provider': 'openai',
                'detected_language': language
            }
        except Exception as e:
            logger.info(f"OpenAI chat response failed: {e}")

    # 2. Try Gemini if configured
    gemini_client = get_gemini_client()
    if gemini_client and not is_fallback:
        try:
            contents = [SYSTEM_EMERGENCY_PROMPT]
            if conversation_history:
                for msg in conversation_history[-6:]:
                    role = "user" if msg.sender == "user" else "model"
                    contents.append(f"{role}: {msg.message}")
            contents.append(f"user: (Language: {language}) {user_message}")

            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config={'temperature': 0.2}
            )
            bot_text = response.text.strip()
            
            disclaimer = "\n\n⚠️ *ResQAI provides AI-assisted safety guidance and does not replace official dispatchers. In an immediate life-threatening emergency, dial 112.*"
            if "112" not in bot_text:
                bot_text += disclaimer

            return {
                'response': bot_text,
                'category': category,
                'urgency': urgency,
                'is_fallback': False,
                'provider': 'gemini',
                'detected_language': language
            }
        except Exception as e:
            logger.info(f"Gemini chat response failed: {e}")

    # 3. Deterministic Rule-Based Fallback
    safety_instructions = get_safety_instructions(category, language=language)
    
    urgency_headers = {
        'Critical': "🚨 **CRITICAL EMERGENCY ALERT** — Immediate action required!",
        'High': "⚠️ **HIGH PRIORITY EMERGENCY** — Take precautions immediately.",
        'Medium': "ℹ️ **EMERGENCY ASSISTANCE GUIDANCE**",
        'Low': "ℹ️ **SAFETY & RELIEF INFORMATION**"
    }
    header = urgency_headers.get(urgency, urgency_headers['Medium'])
    
    fallback_message = (
        f"{header}\n\n"
        f"**Immediate Safety Action for {category.replace('_', ' ').title()}:**\n"
        f"{safety_instructions}\n\n"
        f"📞 **Official Emergency Helpline: Dial 112** (Pan-India)\n"
        f"• Ambulance: 102 / 108\n"
        f"• Fire: 101\n"
        f"• Police: 100\n"
        f"• NDRF Disaster Helpline: 1078\n\n"
        f"📌 *Need human responders? Please click 'Submit Emergency Report' to broadcast your coordinates.*"
    )

    return {
        'response': fallback_message,
        'category': category,
        'urgency': urgency,
        'is_fallback': True,
        'provider': 'rule_based',
        'detected_language': language
    }


def get_ai_emergency_response(user_message, language='en'):
    """Convenience alias for generate_chat_response."""
    res = generate_chat_response(user_message, language=language)
    return {
        'reply': res.get('response'),
        'category': res.get('category'),
        'urgency': res.get('urgency'),
        'is_fallback': res.get('is_fallback')
    }


class AIService:
    """Pluggable object-oriented interface for AI emergency operations."""
    def __init__(self, api_key=None, model=None):
        self.api_key = api_key
        self.model = model

    def triage_report(self, text, language='en'):
        return classify_and_triage(text, language=language)

    def generate_emergency_advice(self, text, language='en'):
        return get_ai_emergency_response(text, language=language)

