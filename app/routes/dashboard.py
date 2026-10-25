from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models.incident import EmergencyReport
from app.models.notification import UserNotification
from app.models.alert import EmergencyAlert

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """User dashboard computed dynamically from live database records."""
    user_reports_q = EmergencyReport.query.filter_by(user_id=current_user.id)
    
    total_reports = user_reports_q.count()
    active_reports = user_reports_q.filter(
        EmergencyReport.status.in_(['Submitted', 'Under Review', 'Assigned', 'In Progress'])
    ).count()
    resolved_reports = user_reports_q.filter_by(status='Resolved').count()
    recent_reports = user_reports_q.order_by(EmergencyReport.created_at.desc()).limit(5).all()
    
    notifications = UserNotification.query.filter_by(
        user_id=current_user.id
    ).order_by(UserNotification.created_at.desc()).limit(6).all()
    
    active_alerts = EmergencyAlert.query.filter_by(
        is_active=True
    ).order_by(EmergencyAlert.created_at.desc()).limit(4).all()

    stats = {
        'total_reports': total_reports,
        'active_reports': active_reports,
        'resolved_reports': resolved_reports,
        'unread_notifications': current_user.notifications.filter_by(is_read=False).count()
    }

    return render_template(
        'dashboard/user_dashboard.html',
        stats=stats,
        recent_reports=recent_reports,
        notifications=notifications,
        active_alerts=active_alerts
    )
