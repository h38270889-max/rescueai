from datetime import datetime, timezone
import uuid
from extensions import db

def utcnow():
    return datetime.now(timezone.utc)

def generate_alert_id():
    date_str = datetime.now().strftime('%Y%m%d')
    unique_suffix = uuid.uuid4().hex[:5].upper()
    return f"ALT-{date_str}-{unique_suffix}"

class EmergencyAlert(db.Model):
    """Emergency broadcast alerts issued by authorized emergency coordinators or admins."""
    __tablename__ = 'emergency_alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.String(30), unique=True, nullable=False, index=True, default=generate_alert_id)
    created_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(20), default='High', nullable=False)  # Critical, High, Medium
    
    # Broadcast Audience Targeting
    target_audience = db.Column(db.String(50), default='all', nullable=False)  # 'all', 'region', 'category'
    target_region = db.Column(db.String(100), nullable=True)
    target_category = db.Column(db.String(50), nullable=True)
    
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    creator = db.relationship('User', foreign_keys=[created_by_user_id], backref=db.backref('created_alerts', lazy='dynamic'))
    notifications = db.relationship('UserNotification', backref='alert', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def badge_class(self):
        mapping = {
            'Critical': 'danger',
            'High': 'warning text-dark',
            'Medium': 'info text-dark'
        }
        return mapping.get(self.urgency, 'secondary')
