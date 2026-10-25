from datetime import datetime, timezone
from extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class AuditLog(db.Model):
    """System-wide security and operational audit trail."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=True)  # incident, alert, user, system
    target_id = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)

    user = db.relationship('User', foreign_keys=[user_id])

    @staticmethod
    def log(action, user_id=None, target_type=None, target_id=None, ip_address=None, details=None):
        """Helper method to append an audit log entry in current transaction."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            ip_address=ip_address,
            details=details
        )
        db.session.add(entry)
        return entry
