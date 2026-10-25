from datetime import datetime, timezone
from extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class ChatConversation(db.Model):
    """Chat session for ResQAI assistant conversations."""
    __tablename__ = 'chat_conversations'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    title = db.Column(db.String(120), default='Emergency Support Conversation', nullable=False)
    language = db.Column(db.String(10), default='en', nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')


class ChatMessage(db.Model):
    """Individual message exchange between user and ResQAI emergency assistant."""
    __tablename__ = 'chat_messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('chat_conversations.id', ondelete='CASCADE'), nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    message = db.Column(db.Text, nullable=False)
    
    # AI Emergency Triage Meta
    detected_language = db.Column(db.String(10), nullable=True)
    detected_category = db.Column(db.String(50), nullable=True)
    detected_urgency = db.Column(db.String(20), nullable=True)
    is_fallback = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'sender': self.sender,
            'message': self.message,
            'detected_language': self.detected_language,
            'detected_category': self.detected_category,
            'detected_urgency': self.detected_urgency,
            'is_fallback': self.is_fallback,
            'created_at': self.created_at.strftime('%H:%M • %b %d')
        }
