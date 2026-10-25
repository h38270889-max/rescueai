import uuid
from flask import Blueprint, render_template, request, jsonify, session
from flask_login import current_user
from extensions import db
from app.models.chat import ChatConversation, ChatMessage
from app.services.ai_service import generate_chat_response

chatbot_bp = Blueprint('chatbot', __name__)

def get_or_create_conversation(session_id, language='en'):
    """Get active conversation or create a new session."""
    user_id = current_user.id if current_user.is_authenticated else None
    
    conv = None
    if user_id:
        conv = ChatConversation.query.filter_by(user_id=user_id).order_by(ChatConversation.updated_at.desc()).first()
    
    if not conv and session_id:
        conv = ChatConversation.query.filter_by(session_id=session_id).first()

    if not conv:
        conv = ChatConversation(
            session_id=session_id or uuid.uuid4().hex,
            user_id=user_id,
            language=language
        )
        db.session.add(conv)
        db.session.commit()
        
    return conv

@chatbot_bp.route('/chatbot')
def index():
    """Render modern emergency chat interface."""
    if 'chat_session_id' not in session:
        session['chat_session_id'] = uuid.uuid4().hex

    suggested_queries = [
        "What should I do during a flood?",
        "How can I stay safe during an earthquake?",
        "There is a fire in my building. What should I do?",
        "Someone is injured with heavy bleeding. How to help?",
        "I am trapped inside an elevator.",
        "How do I request emergency rescue or relief shelter?"
    ]

    return render_template(
        'chatbot/chat.html',
        session_id=session['chat_session_id'],
        suggested_queries=suggested_queries
    )


@chatbot_bp.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle chat messages via JSON API with live triage and fallback detection."""
    data = request.get_json(silent=True) or {}
    user_message = data.get('message', '').strip()
    session_id = data.get('session_id') or session.get('chat_session_id') or uuid.uuid4().hex
    language = data.get('language') or session.get('lang', 'en')

    if not user_message:
        return jsonify({'error': 'Message content cannot be empty.'}), 400

    conv = get_or_create_conversation(session_id, language)
    history = conv.messages.order_by(ChatMessage.created_at.asc()).all()

    # 1. Record User Message
    user_msg_record = ChatMessage(
        conversation_id=conv.id,
        sender='user',
        message=user_message,
        detected_language=language
    )
    db.session.add(user_msg_record)

    # 2. Generate Emergency Assistant Response
    ai_result = generate_chat_response(user_message, conversation_history=history, language=language)

    # 3. Record Assistant Reply
    assistant_msg_record = ChatMessage(
        conversation_id=conv.id,
        sender='assistant',
        message=ai_result['response'],
        detected_language=language,
        detected_category=ai_result.get('category'),
        detected_urgency=ai_result.get('urgency'),
        is_fallback=ai_result.get('is_fallback', True)
    )
    db.session.add(assistant_msg_record)
    db.session.commit()

    return jsonify({
        'success': True,
        'reply': ai_result['response'],
        'category': ai_result.get('category'),
        'urgency': ai_result.get('urgency'),
        'is_fallback': ai_result.get('is_fallback', True),
        'timestamp': assistant_msg_record.created_at.strftime('%H:%M')
    })


@chatbot_bp.route('/api/chat/history', methods=['GET'])
def api_history():
    """Retrieve chat history for the current session or user."""
    session_id = request.args.get('session_id') or session.get('chat_session_id')
    user_id = current_user.id if current_user.is_authenticated else None

    conv = None
    if user_id:
        conv = ChatConversation.query.filter_by(user_id=user_id).order_by(ChatConversation.updated_at.desc()).first()
    elif session_id:
        conv = ChatConversation.query.filter_by(session_id=session_id).first()

    if not conv:
        return jsonify({'messages': []})

    messages = [m.to_dict() for m in conv.messages.order_by(ChatMessage.created_at.asc()).all()]
    return jsonify({'messages': messages})


@chatbot_bp.route('/api/chat/clear', methods=['POST'])
def api_clear():
    """Clear chat messages in current conversation."""
    session_id = request.json.get('session_id') if request.is_json else session.get('chat_session_id')
    user_id = current_user.id if current_user.is_authenticated else None

    conv = None
    if user_id:
        conv = ChatConversation.query.filter_by(user_id=user_id).first()
    elif session_id:
        conv = ChatConversation.query.filter_by(session_id=session_id).first()

    if conv:
        ChatMessage.query.filter_by(conversation_id=conv.id).delete()
        db.session.commit()

    return jsonify({'success': True, 'message': 'Conversation cleared.'})
