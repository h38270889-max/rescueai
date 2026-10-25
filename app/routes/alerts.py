from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from app.models.alert import EmergencyAlert
from app.models.notification import UserNotification

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts')
def list_alerts():
    """Public list of active and recent emergency broadcast alerts."""
    alerts = EmergencyAlert.query.order_by(
        EmergencyAlert.is_active.desc(),
        EmergencyAlert.created_at.desc()
    ).all()
    return render_template('alerts/list.html', alerts=alerts)


@alerts_bp.route('/alerts/<alert_id>')
def detail(alert_id):
    """View details of a specific emergency alert."""
    alert = EmergencyAlert.query.filter_by(alert_id=alert_id).first_or_404()
    return render_template('alerts/detail.html', alert=alert)


@alerts_bp.route('/notifications')
@login_required
def notifications():
    """User notifications center."""
    notifs = UserNotification.query.filter_by(
        user_id=current_user.id
    ).order_by(UserNotification.created_at.desc()).all()
    return render_template('alerts/notifications.html', notifications=notifs)


@alerts_bp.route('/notifications/<int:notification_id>/read', methods=['POST', 'GET'])
@login_required
def mark_read(notification_id):
    """Mark a notification as read."""
    notif = UserNotification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first_or_404()
    notif.is_read = True
    db.session.commit()

    if request.is_json:
        return jsonify({'success': True, 'notification_id': notification_id})

    # If linked to incident or alert, redirect there
    if notif.incident_id and notif.incident:
        return redirect(url_for('incidents.detail', incident_id=notif.incident.incident_id))
    elif notif.alert_id and notif.alert:
        return redirect(url_for('alerts.detail', alert_id=notif.alert.alert_id))

    return redirect(url_for('alerts.notifications'))


@alerts_bp.route('/notifications/mark-all-read', methods=['POST', 'GET'])
@login_required
def mark_all_read():
    """Mark all unread notifications as read for current user."""
    UserNotification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'info')
    return redirect(url_for('alerts.notifications'))
