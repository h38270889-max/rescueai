from datetime import datetime, timezone
from extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class FamilyContact(db.Model):
    """Trusted contacts designated by users for family safety check-ins."""
    __tablename__ = 'family_contacts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    contact_method = db.Column(db.String(50), default='email', nullable=False)  # 'email', 'phone', 'app_user'
    contact_value = db.Column(db.String(120), nullable=False)
    relationship = db.Column(db.String(50), default='Family Member', nullable=False)
    status = db.Column(db.String(30), default='active', nullable=False)  # 'active', 'revoked'
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('trusted_contacts', lazy='dynamic', cascade='all, delete-orphan'))


class FamilyCheckIn(db.Model):
    """Voluntary 'I am Safe' or distress check-ins dispatched to approved contacts."""
    __tablename__ = 'family_checkins'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(30), default='safe', nullable=False)  # 'safe', 'need_help', 'evacuating'
    message = db.Column(db.Text, nullable=True)
    share_location = db.Column(db.Boolean, default=False, nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    user = db.relationship('User', backref=db.backref('checkins', lazy='dynamic', cascade='all, delete-orphan'))

    @property
    def badge_class(self):
        mapping = {
            'safe': 'success',
            'need_help': 'danger',
            'evacuating': 'warning'
        }
        return mapping.get(self.status, 'secondary')
