"""
Unit and integration tests for ResQAI Spatial Mapping and Privacy Controls.
Verifies that public and ordinary citizens receive generalized GPS coordinates and masked PII,
while authorized responders and administrators receive exact coordinates and contact information.
"""

from extensions import db
from app.models.user import User
from app.models.incident import EmergencyReport
from app.services.map_service import get_map_incidents, get_map_summary_stats

def test_map_privacy_masking_for_public(app, test_users):
    with app.app_context():
        citizen = User.query.get(test_users['citizen1_id'])
        
        # Create an incident with exact GPS and private contact details
        rep = EmergencyReport(
            user_id=citizen.id,
            category="Medical Emergency",
            description="Patient having severe chest pain",
            latitude=19.123456,
            longitude=72.876543,
            contact_name="Aarav Private Submitter",
            contact_phone="+91 99999 88888",
            status="In Progress"
        )
        db.session.add(rep)
        db.session.commit()

        # 1. Query as unauthenticated / public user
        public_markers = get_map_incidents(user=None)
        assert len(public_markers) > 0
        target_marker = next(m for m in public_markers if m['id'] == rep.id)

        assert target_marker['is_approximate'] is True
        assert target_marker['latitude'] == round(19.123456, 2)
        assert target_marker['longitude'] == round(72.876543, 2)
        assert "Protected" in target_marker['contact_name'] or "Confidential" in target_marker['contact_name']
        assert "Hidden" in target_marker['contact_phone']

        # 2. Query as authorized Field Responder
        responder = User.query.get(test_users['responder_id'])
        responder_markers = get_map_incidents(user=responder)
        resp_marker = next(m for m in responder_markers if m['id'] == rep.id)

        assert resp_marker['is_approximate'] is False
        assert resp_marker['latitude'] == 19.123456
        assert resp_marker['longitude'] == 72.876543
        assert resp_marker['contact_name'] == "Aarav Private Submitter"
        assert resp_marker['contact_phone'] == "+91 99999 88888"

def test_map_summary_statistics(app):
    with app.app_context():
        stats = get_map_summary_stats()
        assert 'total_mapped' in stats
        assert 'active_incidents' in stats
        assert 'critical_active' in stats
