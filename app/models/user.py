from datetime import datetime, timezone
import secrets
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    """User account model supporting multi-role access control (user, responder, admin)."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user', 'responder', 'admin'
    preferred_language = db.Column(db.String(10), default='en', nullable=False)
    region = db.Column(db.String(100), nullable=True)  # State/City/District for regional targeting
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    consent_emergency_notifications = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    # Relationships
    reports = db.relationship('EmergencyReport', foreign_keys='EmergencyReport.user_id', backref='reporter', lazy='dynamic')
    assigned_incidents = db.relationship('EmergencyReport', foreign_keys='EmergencyReport.assigned_responder_id', backref='assigned_responder', lazy='dynamic')
    notifications = db.relationship('UserNotification', backref='recipient', lazy='dynamic', cascade='all, delete-orphan')
    conversations = db.relationship('ChatConversation', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Securely hash and store user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_responder(self):
        return self.role in ('responder', 'admin')

    def __repr__(self):
        return f"<User {self.id}: {self.email} ({self.role})>"


class PasswordResetToken(db.Model):
    """Single-use, expiring token for secure password recovery."""
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('reset_tokens', lazy='dynamic', cascade='all, delete-orphan'))

    @staticmethod
    def generate_token_string():
        return secrets.token_urlsafe(32)

    def is_valid(self):
        """Check if token is neither used nor expired."""
        now = datetime.now(timezone.utc)
        # Handle naive or aware datetimes
        token_expires = self.expires_at
        if token_expires.tzinfo is None:
            token_expires = token_expires.replace(tzinfo=timezone.utc)
        return (not self.used) and (token_expires > now)
