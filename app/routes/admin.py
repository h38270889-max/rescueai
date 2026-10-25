import csv
from io import StringIO
from datetime import datetime, timedelta, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, abort
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from app.models.incident import EmergencyReport, IncidentStatusHistory, PotentialDuplicateMatch
from app.models.alert import EmergencyAlert
from app.models.user import User
from app.models.audit import AuditLog
from app.forms.alert_forms import CreateAlertForm
from app.forms.incident_forms import IncidentUpdateForm
from app.services.notification_service import dispatch_emergency_alert, send_incident_status_notification
from app.services.duplicate_service import review_duplicate_match
from app.utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
@login_required
@admin_required
def before_request():
    """Ensure all admin routes are strictly guarded."""
    pass

@admin_bp.route('/')
def dashboard():
    """Administrator Command & Control Overview."""
    total_incidents = EmergencyReport.query.count()
    new_incidents = EmergencyReport.query.filter_by(status='Submitted').count()
    high_priority = EmergencyReport.query.filter(
        EmergencyReport.ai_suggested_priority.in_(['Critical', 'High']),
        EmergencyReport.status != 'Resolved'
    ).count()
    in_progress = EmergencyReport.query.filter_by(status='In Progress').count()
    resolved = EmergencyReport.query.filter_by(status='Resolved').count()
    
    total_alerts = EmergencyAlert.query.count()
    active_alerts = EmergencyAlert.query.filter_by(is_active=True).count()
    total_users = User.query.count()

    recent_incidents = EmergencyReport.query.order_by(EmergencyReport.created_at.desc()).limit(8).all()
    recent_audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(6).all()

    stats = {
        'total_incidents': total_incidents,
        'new_incidents': new_incidents,
        'high_priority': high_priority,
        'in_progress': in_progress,
        'resolved': resolved,
        'total_alerts': total_alerts,
        'active_alerts': active_alerts,
        'total_users': total_users
    }

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_incidents=recent_incidents,
        recent_audits=recent_audits
    )


@admin_bp.route('/incidents')
def incidents():
    """Manage incidents with filtering, search, and priority triage."""
    query = EmergencyReport.query

    category = request.args.get('category')
    status = request.args.get('status')
    priority = request.args.get('priority')
    search = request.args.get('q')

    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(ai_suggested_priority=priority)
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            (EmergencyReport.incident_id.ilike(search_term)) |
            (EmergencyReport.description.ilike(search_term)) |
            (EmergencyReport.location_address.ilike(search_term)) |
            (EmergencyReport.contact_name.ilike(search_term))
        )

    all_incidents = query.order_by(
        EmergencyReport.status == 'Submitted',
        EmergencyReport.created_at.desc()
    ).all()

    return render_template(
        'admin/incidents.html',
        incidents=all_incidents,
        selected_category=category,
        selected_status=status,
        selected_priority=priority,
        search_query=search
    )


@admin_bp.route('/incidents/<incident_id>', methods=['GET', 'POST'])
def incident_detail(incident_id):
    """Review AI classification, assign responder, add notes, and transition status."""
    report = EmergencyReport.query.filter_by(incident_id=incident_id).first_or_404()
    form = IncidentUpdateForm(obj=report)

    # Populate responders dropdown
    responders = User.query.filter(User.role.in_(['responder', 'admin'])).all()
    form.assigned_responder_id.choices = [(0, '-- Unassigned --')] + [(r.id, f"{r.full_name} ({r.role.title()})") for r in responders]

    if request.method == 'GET':
        form.assigned_responder_id.data = report.assigned_responder_id or 0
        form.status.data = report.status
        form.responder_notes.data = report.responder_notes or ''

    if form.validate_on_submit():
        old_status = report.status
        new_status = form.status.data
        new_assigned_id = form.assigned_responder_id.data if form.assigned_responder_id.data != 0 else None
        notes = form.responder_notes.data

        report.status = new_status
        report.assigned_responder_id = new_assigned_id
        report.responder_notes = notes

        # If status changed, record in history and notify citizen
        if old_status != new_status or notes:
            history = IncidentStatusHistory(
                incident_id=report.id,
                old_status=old_status,
                new_status=new_status,
                changed_by_user_id=current_user.id,
                notes=notes
            )
            db.session.add(history)
            send_incident_status_notification(report, new_status, notes)

        AuditLog.log(
            action='INCIDENT_UPDATED',
            user_id=current_user.id,
            target_type='incident',
            target_id=report.id,
            details=f"Status changed from {old_status} to {new_status}. Assigned responder: {new_assigned_id}"
        )
        db.session.commit()

        flash(f"Incident {report.incident_id} updated successfully.", 'success')
        return redirect(url_for('admin.incident_detail', incident_id=report.incident_id))

    history = report.status_history.order_by(IncidentStatusHistory.created_at.desc()).all()
    return render_template('admin/incident_detail.html', report=report, form=form, history=history)


@admin_bp.route('/incidents/export/csv')
def export_incidents_csv():
    """Export all incident records as CSV for disaster management reporting."""
    incidents = EmergencyReport.query.order_by(EmergencyReport.created_at.desc()).all()
    
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow([
        'Incident ID', 'Category', 'AI Priority', 'Status',
        'Affected Count', 'Location Address', 'Latitude', 'Longitude',
        'Contact Name', 'Contact Phone', 'Original Language',
        'Description', 'Created At (UTC)'
    ])

    for inc in incidents:
        writer.writerow([
            inc.incident_id,
            inc.category,
            inc.ai_suggested_priority,
            inc.status,
            inc.affected_count,
            inc.location_address or '',
            inc.latitude or '',
            inc.longitude or '',
            inc.contact_name or '',
            inc.contact_phone or '',
            inc.original_language,
            inc.description.replace('\n', ' '),
            inc.created_at.isoformat() if inc.created_at else ''
        ])

    AuditLog.log(
        action='CSV_EXPORT',
        user_id=current_user.id,
        target_type='incident',
        details=f"Exported {len(incidents)} incidents as CSV"
    )
    db.session.commit()

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=resqai_emergency_incidents.csv"}
    )


@admin_bp.route('/alerts')
def alerts():
    """View and manage emergency broadcast alerts."""
    all_alerts = EmergencyAlert.query.order_by(EmergencyAlert.created_at.desc()).all()
    return render_template('admin/alerts.html', alerts=all_alerts)


@admin_bp.route('/alerts/create', methods=['GET', 'POST'])
def create_alert():
    """Create and broadcast an emergency alert to consented users."""
    form = CreateAlertForm()
    if form.validate_on_submit():
        alert = EmergencyAlert(
            created_by_user_id=current_user.id,
            title=form.title.data.strip(),
            category=form.category.data,
            urgency=form.urgency.data,
            target_audience=form.target_audience.data,
            target_region=form.target_region.data.strip() if form.target_region.data else None,
            message=form.message.data.strip(),
            is_active=True
        )
        db.session.add(alert)
        db.session.flush()

        # Broadcast notifications across eligible users
        dispatch_result = dispatch_emergency_alert(alert, current_user_id=current_user.id)

        flash(
            f"Emergency Alert '{alert.title}' broadcasted! "
            f"Delivered in-app to {dispatch_result['in_app_delivered']} users. "
            f"({dispatch_result['push_status']})",
            'success'
        )
        return redirect(url_for('admin.alerts'))

    return render_template('admin/create_alert.html', form=form)


@admin_bp.route('/alerts/<alert_id>/cancel', methods=['POST'])
def cancel_alert(alert_id):
    """Deactivate or cancel an ongoing emergency alert."""
    alert = EmergencyAlert.query.filter_by(alert_id=alert_id).first_or_404()
    alert.is_active = False
    
    AuditLog.log(
        action='ALERT_CANCELLED',
        user_id=current_user.id,
        target_type='alert',
        target_id=alert.id,
        details=f"Alert {alert.alert_id} deactivated by admin"
    )
    db.session.commit()
    
    flash(f"Alert {alert.alert_id} has been deactivated.", 'info')
    return redirect(url_for('admin.alerts'))


@admin_bp.route('/users')
def users():
    """User accounts directory and role administration."""
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=all_users)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
def toggle_user_status(user_id):
    """Activate or deactivate user account."""
    if user_id == current_user.id:
        flash("You cannot deactivate your own administrative account.", 'warning')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    
    AuditLog.log(
        action='USER_STATUS_TOGGLED',
        user_id=current_user.id,
        target_type='user',
        target_id=user.id,
        details=f"User {user.email} active status set to {user.is_active}"
    )
    db.session.commit()

    status_str = "activated" if user.is_active else "deactivated"
    flash(f"User {user.email} has been {status_str}.", 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/set-role', methods=['POST'])
def set_user_role(user_id):
    """Update role for user (user, responder, admin)."""
    if user_id == current_user.id:
        flash("You cannot modify your own administrative role.", 'warning')
        return redirect(url_for('admin.users'))

    new_role = request.form.get('role')
    if new_role not in ['user', 'responder', 'admin']:
        flash("Invalid role specified.", 'danger')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    old_role = user.role
    user.role = new_role
    
    AuditLog.log(
        action='USER_ROLE_CHANGED',
        user_id=current_user.id,
        target_type='user',
        target_id=user.id,
        details=f"User {user.email} role changed from {old_role} to {new_role}"
    )
    db.session.commit()

    flash(f"User {user.email} role updated to {new_role.title()}.", 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/analytics')
def analytics():
    """Visual analytics dashboard using dynamic Chart.js charts."""
    # 1. Incidents by Category
    category_counts = db.session.query(
        EmergencyReport.category, func.count(EmergencyReport.id)
    ).group_by(EmergencyReport.category).all()

    # 2. Incidents by Status
    status_counts = db.session.query(
        EmergencyReport.status, func.count(EmergencyReport.id)
    ).group_by(EmergencyReport.status).all()

    # 3. Incidents by Priority
    priority_counts = db.session.query(
        EmergencyReport.ai_suggested_priority, func.count(EmergencyReport.id)
    ).group_by(EmergencyReport.ai_suggested_priority).all()

    # 4. Language Distribution
    language_counts = db.session.query(
        EmergencyReport.original_language, func.count(EmergencyReport.id)
    ).group_by(EmergencyReport.original_language).all()

    return render_template(
        'admin/analytics.html',
        category_data=dict(category_counts),
        status_data=dict(status_counts),
        priority_data=dict(priority_counts),
        language_data=dict(language_counts)
    )


@admin_bp.route('/duplicates')
def duplicates():
    """Administrator console for reviewing suspected duplicate disaster reports."""
    status_filter = request.args.get('status', 'all')
    query = PotentialDuplicateMatch.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    matches = query.order_by(PotentialDuplicateMatch.created_at.desc()).all()
    pending_count = PotentialDuplicateMatch.query.filter_by(status='pending').count()

    return render_template(
        'admin/duplicates.html',
        matches=matches,
        status_filter=status_filter,
        pending_count=pending_count
    )


@admin_bp.route('/duplicates/<int:match_id>/review', methods=['POST'])
def review_duplicate(match_id):
    """Confirm or reject a potential duplicate match."""
    decision = request.form.get('decision')
    notes = request.form.get('notes', '').strip()

    if decision not in ['confirmed_duplicate', 'rejected_distinct']:
        flash('Invalid review decision.', 'danger')
        return redirect(url_for('admin.duplicates'))

    match = review_duplicate_match(
        match_id=match_id,
        decision=decision,
        reviewer_user_id=current_user.id,
        notes=notes or None
    )

    action_label = "Confirmed Duplicate" if decision == 'confirmed_duplicate' else "Marked Distinct"
    flash(f"Incident comparison #{match.id} successfully reviewed as '{action_label}'.", 'success')
    return redirect(url_for('admin.duplicates'))

