from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from app.models.incident import EmergencyReport, IncidentStatusHistory
from app.models.alert import EmergencyAlert
from app.models.audit import AuditLog
from app.services.notification_service import send_incident_status_notification
from app.utils.decorators import responder_required

responder_bp = Blueprint('responder', __name__, url_prefix='/responder')

@responder_bp.before_request
@login_required
@responder_required
def before_request():
    """Restrict responder blueprint to authorized responders and admins."""
    pass

@responder_bp.route('/')
def dashboard():
    """Responder active dispatch desk."""
    # My assigned incidents
    my_assigned = EmergencyReport.query.filter_by(
        assigned_responder_id=current_user.id
    ).order_by(EmergencyReport.updated_at.desc()).all()

    # Unassigned incidents needing dispatch
    unassigned = EmergencyReport.query.filter_by(
        assigned_responder_id=None
    ).filter(
        EmergencyReport.status.in_(['Submitted', 'Under Review'])
    ).order_by(
        EmergencyReport.ai_suggested_priority == 'Critical',
        EmergencyReport.created_at.desc()
    ).limit(10).all()

    # Active broadcast alerts
    active_alerts = EmergencyAlert.query.filter_by(is_active=True).all()

    return render_template(
        'responder/dashboard.html',
        assigned_incidents=my_assigned,
        unassigned_incidents=unassigned,
        active_alerts=active_alerts
    )


@responder_bp.route('/incidents/<incident_id>', methods=['GET', 'POST'])
def incident_detail(incident_id):
    """Responder incident inspection and field action update."""
    report = EmergencyReport.query.filter_by(incident_id=incident_id).first_or_404()

    if request.method == 'POST':
        action = request.form.get('action')
        notes = request.form.get('notes', '').strip()
        new_status = request.form.get('status', report.status)

        old_status = report.status

        if action == 'claim':
            report.assigned_responder_id = current_user.id
            report.status = 'Assigned'
            flash(f"You have claimed responsibility for incident {report.incident_id}.", 'info')
        else:
            report.status = new_status
            if notes:
                report.responder_notes = notes

        # Record history if status or notes changed
        history = IncidentStatusHistory(
            incident_id=report.id,
            old_status=old_status,
            new_status=report.status,
            changed_by_user_id=current_user.id,
            notes=notes or f"Updated by responder {current_user.full_name}"
        )
        db.session.add(history)
        
        # Notify citizen
        send_incident_status_notification(report, report.status, notes)

        AuditLog.log(
            action='RESPONDER_INCIDENT_UPDATE',
            user_id=current_user.id,
            target_type='incident',
            target_id=report.id,
            details=f"Responder updated incident {report.incident_id} to {report.status}."
        )
        db.session.commit()

        flash(f"Incident {report.incident_id} updated.", 'success')
        return redirect(url_for('responder.incident_detail', incident_id=report.incident_id))

    history = report.status_history.order_by(IncidentStatusHistory.created_at.desc()).all()
    return render_template('responder/incident_detail.html', report=report, history=history)
