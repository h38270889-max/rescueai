"""
ResQAI Family Safety Check-In Blueprint.
Allows citizens to manage trusted family contacts and broadcast voluntary 'I am Safe' status updates.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.family import FamilyContact, FamilyCheckIn
from app.services.family_service import (
    add_family_contact,
    revoke_family_contact,
    send_family_checkin
)

family_bp = Blueprint('family', __name__, url_prefix='/family')


@family_bp.route('/')
@login_required
def index():
    """Display user's trusted contacts and safety check-in history."""
    contacts = FamilyContact.query.filter_by(
        user_id=current_user.id
    ).order_by(FamilyContact.created_at.desc()).all()

    checkins = FamilyCheckIn.query.filter_by(
        user_id=current_user.id
    ).order_by(FamilyCheckIn.created_at.desc()).limit(20).all()

    active_contacts_count = sum(1 for c in contacts if c.status == 'active')

    return render_template(
        'family/index.html',
        contacts=contacts,
        checkins=checkins,
        active_contacts_count=active_contacts_count
    )


@family_bp.route('/contact/add', methods=['POST'])
@login_required
def add_contact():
    """Add a new trusted family or emergency contact."""
    name = request.form.get('name', '').strip()
    contact_method = request.form.get('contact_method', 'email').strip()
    contact_value = request.form.get('contact_value', '').strip()
    relationship = request.form.get('relationship', 'Family Member').strip()

    if not name or not contact_value:
        flash('Contact name and communication address/number are required.', 'warning')
        return redirect(url_for('family.index'))

    add_family_contact(
        user_id=current_user.id,
        name=name,
        contact_method=contact_method,
        contact_value=contact_value,
        relationship=relationship or 'Family Member'
    )
    flash(f"Successfully added {name} as a trusted emergency contact.", 'success')
    return redirect(url_for('family.index'))


@family_bp.route('/contact/<int:contact_id>/revoke', methods=['POST'])
@login_required
def revoke_contact(contact_id):
    """Revoke sharing permissions for a contact."""
    contact = revoke_family_contact(current_user.id, contact_id)
    flash(f"Permissions revoked for {contact.name}. They will no longer receive your safety broadcasts.", 'info')
    return redirect(url_for('family.index'))


@family_bp.route('/checkin', methods=['POST'])
@login_required
def checkin():
    """Submit a voluntary safety status broadcast to trusted contacts."""
    status = request.form.get('status', 'safe')
    message = request.form.get('message', '').strip()
    share_location = request.form.get('share_location') == '1'
    lat = request.form.get('latitude')
    lng = request.form.get('longitude')
    location_name = request.form.get('location_name', '').strip()

    lat_val = float(lat) if lat and lat.strip() else None
    lng_val = float(lng) if lng and lng.strip() else None

    result = send_family_checkin(
        user_id=current_user.id,
        status=status,
        message=message or None,
        share_location=share_location,
        lat=lat_val,
        lng=lng_val,
        location_name=location_name or None
    )

    status_labels = {
        'safe': 'I AM SAFE',
        'need_help': 'NEED ASSISTANCE',
        'evacuating': 'EVACUATING'
    }
    label = status_labels.get(status, status.upper())

    if result and result.get('notifications_created', 0) > 0:
        flash(f"Status '{label}' broadcast successfully to your {result['notifications_created']} registered family contacts!", 'success')
    else:
        flash(f"Status '{label}' recorded on your safety timeline. (Tip: When your contacts register with their email, they receive automatic alerts).", 'info')

    return redirect(url_for('family.index'))
