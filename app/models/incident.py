from datetime import datetime, timezone
import uuid
from extensions import db

def utcnow():
    return datetime.now(timezone.utc)

def generate_incident_id():
    """Generate a clean, professional incident ID like INC-20261025-8A3F."""
    date_str = datetime.now().strftime('%Y%m%d')
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"INC-{date_str}-{unique_suffix}"

class EmergencyReport(db.Model):
    """Emergency incident report model with AI triage, location, responder assignment, and duplicate tracking."""
    __tablename__ = 'emergency_reports'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.String(30), unique=True, nullable=False, index=True, default=generate_incident_id)
    idempotency_key = db.Column(db.String(64), unique=True, nullable=True, index=True)
    
    # Submitter (nullable for anonymous / emergency walk-in submissions)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    
    # Core Incident Data
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    original_language = db.Column(db.String(10), default='en', nullable=False)
    translated_description = db.Column(db.Text, nullable=True)
    translation_confidence = db.Column(db.Float, nullable=True)
    translation_service = db.Column(db.String(50), default='none', nullable=True)
    
    # Contact & Location
    contact_name = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(30), nullable=True)
    location_address = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    affected_count = db.Column(db.Integer, default=1, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    
    # Status & Triage
    # Status values: Submitted, Under Review, Assigned, In Progress, Resolved, Closed
    status = db.Column(db.String(30), default='Submitted', nullable=False, index=True)
    
    # AI Classification & Urgency
    ai_suggested_category = db.Column(db.String(50), nullable=True)
    ai_suggested_priority = db.Column(db.String(20), default='Medium', nullable=False)  # Critical, High, Medium, Low
    ai_classification_explanation = db.Column(db.Text, nullable=True)
    is_high_risk = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Duplicate Incident Detection Fields
    is_potential_duplicate = db.Column(db.Boolean, default=False, nullable=False, index=True)
    potential_duplicate_of_id = db.Column(db.Integer, db.ForeignKey('emergency_reports.id', ondelete='SET NULL'), nullable=True)
    duplicate_similarity_score = db.Column(db.Float, nullable=True)
    duplicate_match_reason = db.Column(db.String(255), nullable=True)
    duplicate_review_status = db.Column(db.String(30), default='none', nullable=False)  # 'none', 'flagged', 'confirmed_duplicate', 'rejected_distinct'

    # Assignment & Responder Workflow
    assigned_responder_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    responder_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    status_history = db.relationship('IncidentStatusHistory', backref='incident', lazy='dynamic', cascade='all, delete-orphan')
    potential_duplicate_of = db.relationship('EmergencyReport', remote_side=[id], backref=db.backref('suspected_duplicates', lazy='dynamic'))

    @property
    def badge_class(self):
        """Bootstrap color class mapping for UI status badges."""
        mapping = {
            'Submitted': 'secondary',
            'Under Review': 'warning',
            'Assigned': 'info',
            'In Progress': 'primary',
            'Resolved': 'success',
            'Closed': 'dark'
        }
        return mapping.get(self.status, 'secondary')

    @property
    def priority_badge_class(self):
        """Bootstrap color class mapping for urgency."""
        mapping = {
            'Critical': 'danger',
            'High': 'warning text-dark',
            'Medium': 'info text-dark',
            'Low': 'secondary'
        }
        return mapping.get(self.ai_suggested_priority, 'secondary')

    def to_dict(self):
        """Serialize report for API/Offline Sync responses and Leaflet maps."""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'idempotency_key': self.idempotency_key,
            'category': self.category,
            'description': self.description,
            'original_language': self.original_language,
            'translated_description': self.translated_description,
            'status': self.status,
            'priority': self.ai_suggested_priority,
            'location_address': self.location_address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'affected_count': self.affected_count,
            'is_potential_duplicate': self.is_potential_duplicate,
            'duplicate_review_status': self.duplicate_review_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PotentialDuplicateMatch(db.Model):
    """Pairwise suspected duplicate incident log for human administrator review."""
    __tablename__ = 'potential_duplicate_matches'

    id = db.Column(db.Integer, primary_key=True)
    incident_a_id = db.Column(db.Integer, db.ForeignKey('emergency_reports.id', ondelete='CASCADE'), nullable=False)
    incident_b_id = db.Column(db.Integer, db.ForeignKey('emergency_reports.id', ondelete='CASCADE'), nullable=False)
    similarity_score = db.Column(db.Float, nullable=False)
    distance_km = db.Column(db.Float, nullable=True)
    time_diff_hours = db.Column(db.Float, nullable=True)
    match_reason = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), default='pending', nullable=False)  # 'pending', 'confirmed_duplicate', 'rejected_distinct'
    reviewed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    review_notes = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    incident_a = db.relationship('EmergencyReport', foreign_keys=[incident_a_id])
    incident_b = db.relationship('EmergencyReport', foreign_keys=[incident_b_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_user_id])


class IncidentStatusHistory(db.Model):
    """Audit log tracking every status transition and responder reassignment."""
    __tablename__ = 'incident_status_history'

    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('emergency_reports.id', ondelete='CASCADE'), nullable=False)
    old_status = db.Column(db.String(30), nullable=True)
    new_status = db.Column(db.String(30), nullable=False)
    changed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    changed_by = db.relationship('User', foreign_keys=[changed_by_user_id])
