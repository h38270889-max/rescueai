"""
ResQAI Family Safety Check-In Service.
Manages trusted contacts, voluntary 'I am Safe' status dispatches,
and in-app notification routing to approved family members.
"""

from extensions import db
from app.models.family import FamilyContact, FamilyCheckIn
from app.models.notification import UserNotification
from app.models.user import User
from app.models.audit import AuditLog

def add_family_contact(user_id, name, contact_method, contact_value, relationship='Family Member'):
    """Add a new trusted family or emergency contact."""
    contact = FamilyContact(
        user_id=user_id,
        name=name.strip(),
        contact_method=contact_method,
        contact_value=contact_value.strip().lower(),
        relationship=relationship.strip(),
        status='active'
    )
    db.session.add(contact)
    db.session.commit()

    AuditLog.log(
        action='FAMILY_CONTACT_ADDED',
        user_id=user_id,
        target_type='family_contact',
        target_id=contact.id,
        details=f"Added trusted contact: {contact.name} ({contact.relationship})"
    )
    db.session.commit()
    return contact

def revoke_family_contact(user_id, contact_id):
    """Revoke sharing permissions for a trusted contact."""
    contact = FamilyContact.query.filter_by(id=contact_id, user_id=user_id).first_or_404()
    contact.status = 'revoked'
    db.session.commit()

    AuditLog.log(
        action='FAMILY_CONTACT_REVOKED',
        user_id=user_id,
        target_type='family_contact',
        target_id=contact.id,
        details=f"Revoked permissions for: {contact.name}"
    )
    db.session.commit()
    return contact

def send_family_checkin(user_id, status='safe', message=None, share_location=False, lat=None, lng=None, location_name=None):
    """
    Record a voluntary safety check-in and dispatch in-app notifications to approved contacts.
    status: 'safe' | 'need_help' | 'evacuating'
    """
    user = User.query.get(user_id)
    if not user:
        return None

    checkin = FamilyCheckIn(
        user_id=user_id,
        status=status,
        message=message,
        share_location=share_location,
        latitude=lat if share_location else None,
        longitude=lng if share_location else None,
        location_name=location_name if share_location else None
    )
    db.session.add(checkin)
    db.session.flush()

    # Route notifications to active contacts
    active_contacts = FamilyContact.query.filter_by(user_id=user_id, status='active').all()
    notifications_created = 0

    status_titles = {
        'safe': f"🟢 Family Update: {user.full_name} is SAFE",
        'need_help': f"🚨 Family Alert: {user.full_name} NEEDS ASSISTANCE",
        'evacuating': f"⚠️ Family Alert: {user.full_name} is EVACUATING"
    }
    title = status_titles.get(status, f"Family Status Update: {user.full_name}")

    notif_msg = f"{user.full_name} sent a status update: '{status.upper().replace('_', ' ')}'."
    if message:
        notif_msg += f"\nMessage: {message}"
    if share_location and location_name:
        notif_msg += f"\nLocation: {location_name}"

    for c in active_contacts:
        # If the contact is registered on ResQAI, deliver an in-app notification
        matched_user = User.query.filter_by(email=c.contact_value).first()
        if matched_user:
            notif = UserNotification(
                user_id=matched_user.id,
                title=title,
                message=notif_msg,
                delivery_channel='in_app',
                delivery_status='delivered',
                delivery_details=f"From trusted contact: {user.full_name}"
            )
            db.session.add(notif)
            notifications_created += 1

    AuditLog.log(
        action='FAMILY_CHECKIN_SENT',
        user_id=user_id,
        target_type='family_checkin',
        target_id=checkin.id,
        details=f"Check-in status: {status}. Notifications created: {notifications_created}"
    )
    db.session.commit()

    return {
        'checkin': checkin,
        'notifications_created': notifications_created,
        'contacts_count': len(active_contacts)
    }
