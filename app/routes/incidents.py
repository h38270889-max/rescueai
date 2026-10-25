from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from extensions import db
from app.models.incident import EmergencyReport, IncidentStatusHistory
from app.models.audit import AuditLog
from app.forms.incident_forms import EmergencyReportForm
from app.services.incident_service import submit_emergency_incident, trigger_one_tap_sos
from app.utils.helpers import save_uploaded_image

incidents_bp = Blueprint('incidents', __name__)

@incidents_bp.route('/report', methods=['GET', 'POST'])
def report():
    """Submit a new emergency report with AI triage and multilingual translation."""
    form = EmergencyReportForm()
    
    # Pre-fill contact details if user is logged in
    if request.method == 'GET' and current_user.is_authenticated:
        form.contact_name.data = current_user.full_name
        form.contact_phone.data = current_user.phone or ''
        form.original_language.data = current_user.preferred_language

    if form.validate_on_submit():
        # Handle file upload safely
        image_filename = None
        if form.image.data:
            image_filename = save_uploaded_image(form.image.data)

        desc = form.description.data.strip()
        lang = form.original_language.data

        report, is_dup, match_cand, match_rec = submit_emergency_incident(
            description=desc,
            category=form.category.data,
            original_language=lang,
            contact_name=form.contact_name.data.strip() if form.contact_name.data else None,
            contact_phone=form.contact_phone.data.strip() if form.contact_phone.data else None,
            location_address=form.location_address.data.strip() if form.location_address.data else None,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            affected_count=form.affected_count.data,
            image_filename=image_filename,
            user_id=current_user.id if current_user.is_authenticated else None,
            client_ip=request.remote_addr
        )

        dup_notice = " (Note: Potential duplicate detected; flagged for responder review)." if is_dup else ""
        flash(
            f"Emergency report filed successfully! Your Incident ID is {report.incident_id}. "
            f"Triage Priority: {report.ai_suggested_priority}.{dup_notice}",
            'success'
        )
        return redirect(url_for('incidents.detail', incident_id=report.incident_id))

    return render_template('incidents/report.html', form=form)


@incidents_bp.route('/sos', methods=['POST'])
def trigger_sos():
    """Rapid One-Tap SOS emergency beacon endpoint."""
    if request.is_json:
        data = request.get_json() or {}
        lat = data.get('latitude')
        lng = data.get('longitude')
        phone = data.get('phone')
        name = data.get('name')
        lang = data.get('language', 'en')
    else:
        lat = request.form.get('latitude')
        lng = request.form.get('longitude')
        phone = request.form.get('phone')
        name = request.form.get('name')
        lang = request.form.get('language', 'en')

    lat_val = float(lat) if lat is not None and str(lat).strip() != '' else None
    lng_val = float(lng) if lng is not None and str(lng).strip() != '' else None

    report = trigger_one_tap_sos(
        latitude=lat_val,
        longitude=lng_val,
        user=current_user,
        contact_phone=phone,
        contact_name=name,
        client_ip=request.remote_addr,
        language=lang
    )

    if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({
            'status': 'success',
            'incident_id': report.incident_id,
            'priority': report.ai_suggested_priority,
            'message': 'Distress beacon activated. Emergency response queued.'
        })

    flash(f"ONE-TAP SOS BEACON TRANSMITTED! Incident ID: {report.incident_id}. Responders alerted.", 'danger')
    return redirect(url_for('incidents.detail', incident_id=report.incident_id))


@incidents_bp.route('/my-reports')
@login_required
def my_reports():
    """List all emergency incidents submitted by the logged-in user."""
    reports = EmergencyReport.query.filter_by(
        user_id=current_user.id
    ).order_by(EmergencyReport.created_at.desc()).all()
    return render_template('incidents/list.html', reports=reports)


@incidents_bp.route('/<incident_id>')
def detail(incident_id):
    """View detailed tracking timeline and triage information for a specific incident."""
    report = EmergencyReport.query.filter_by(incident_id=incident_id).first_or_404()

    # Access control: users can only view their own reports unless responder/admin
    if current_user.is_authenticated:
        if not (report.user_id == current_user.id or current_user.is_responder or current_user.is_admin):
            flash('Access denied: You do not have permission to view other users\' private incident records.', 'danger')
            abort(403)
    else:
        # If user is guest and submitted in this session (or checking public incident tracker)
        pass

    history = report.status_history.order_by(IncidentStatusHistory.created_at.asc()).all()
    return render_template('incidents/detail.html', report=report, history=history)
