"""
Unit and integration tests for ResQAI Family Safety Center.
Validates trusted contact management, voluntary status check-ins,
location sharing consent, and automated in-app family notifications.
"""

from extensions import db
from app.models.family import FamilyContact, FamilyCheckIn
from app.models.notification import UserNotification
from app.services.family_service import (
    add_family_contact,
    revoke_family_contact,
    send_family_checkin
)

def test_add_and_revoke_family_contact(app, test_users):
    with app.app_context():
        user_id = test_users['citizen1_id']
        contact = add_family_contact(
            user_id=user_id,
            name="Brother",
            contact_method="email",
            contact_value="brother@example.com",
            relationship="Sibling"
        )
        assert contact.id is not None
        assert contact.status == 'active'

        # Revoke permissions
        revoked = revoke_family_contact(user_id=user_id, contact_id=contact.id)
        assert revoked.status == 'revoked'

def test_voluntary_safe_checkin_broadcasts_to_registered_contact(app, test_users):
    with app.app_context():
        citizen1_id = test_users['citizen1_id']
        citizen2_id = test_users['citizen2_id']  # Registered with email citizen2@example.com

        # citizen1 adds citizen2 as trusted contact
        add_family_contact(
            user_id=citizen1_id,
            name="Sister",
            contact_method="email",
            contact_value="citizen2@example.com",
            relationship="Sister"
        )

        # citizen1 sends a 'safe' check-in with GPS location
        res = send_family_checkin(
            user_id=citizen1_id,
            status='safe',
            message="At relief camp with water and food.",
            share_location=True,
            lat=19.0760,
            lng=72.8777,
            location_name="Relief Base Alpha"
        )

        assert res['checkin'].id is not None
        assert res['notifications_created'] == 1

        # Verify notification delivered to citizen2
        notif = UserNotification.query.filter_by(user_id=citizen2_id).first()
        assert notif is not None
        assert "SAFE" in notif.title
        assert "Relief Base Alpha" in notif.message

def test_checkin_without_location_sharing_omits_coordinates(app, test_users):
    with app.app_context():
        citizen1_id = test_users['citizen1_id']
        res = send_family_checkin(
            user_id=citizen1_id,
            status='need_help',
            message="Phone low battery",
            share_location=False,
            lat=19.1234,
            lng=72.5678
        )
        checkin = res['checkin']
        assert checkin.latitude is None
        assert checkin.longitude is None
        assert checkin.status == 'need_help'
