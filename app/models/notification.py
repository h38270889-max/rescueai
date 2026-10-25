from datetime import datetime, timezone
from extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class UserNotification(db.Model):
    """In-app and channel notifications dispatched to users."""
    __tablename__ = 'user_notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('emergency_alerts.id', ondelete='CASCADE'), nullable=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('emergency_reports.id', ondelete='CASCADE'), nullable=True)
    
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Channel and delivery status
    delivery_channel = db.Column(db.String(30), default='in_app', nullable=False)  # in_app, push, email, sms
    delivery_status = db.Column(db.String(30), default='delivered', nullable=False)  # delivered, pending, failed
    delivery_details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    incident = db.relationship('EmergencyReport', foreign_keys=[incident_id])


class PushSubscription(db.Model):
    """Web Push notification subscriptions for browser-based alerts."""
    __tablename__ = 'push_subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=True)
    endpoint = db.Column(db.Text, nullable=False, unique=True)
    p256dh_key = db.Column(db.Text, nullable=False)
    auth_key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
