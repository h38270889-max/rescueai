from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from flask_login import current_user
from extensions import db
from app.models.alert import EmergencyAlert
from app.models.incident import EmergencyReport

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page featuring emergency reporting CTA, AI chatbot entry, and active alerts."""
    active_alerts = EmergencyAlert.query.filter_by(is_active=True).order_by(EmergencyAlert.created_at.desc()).limit(5).all()
    recent_stats = {
        'total_incidents': EmergencyReport.query.count(),
        'resolved_incidents': EmergencyReport.query.filter_by(status='Resolved').count(),
        'active_alerts': EmergencyAlert.query.filter_by(is_active=True).count()
    }
    return render_template('landing.html', active_alerts=active_alerts, stats=recent_stats)

@main_bp.route('/set-language/<lang_code>')
def set_language(lang_code):
    """Update preferred interface language in session and user profile if authenticated."""
    supported = current_app.config.get('SUPPORTED_LANGUAGES', {})
    if lang_code in supported:
        session['lang'] = lang_code
        if current_user.is_authenticated:
            current_user.preferred_language = lang_code
            db.session.commit()
        flash(f"Language changed to {supported[lang_code]['native']} ({supported[lang_code]['name']}).", 'info')
    
    # Redirect back to referring page safely
    referrer = request.referrer
    if referrer and request.host in referrer:
        return redirect(referrer)
    return redirect(url_for('main.index'))

@main_bp.route('/offline-guide')
def offline_guide():
    """Offline survival handbook cached by Service Worker for immediate emergency access."""
    return render_template('offline_guide.html')

@main_bp.route('/contact')
def contact():
    """Pan-India and regional emergency helplines directory."""
    return render_template('contact.html')

@main_bp.route('/about')
def about():
    """About ResQAI mission, architecture, and safety disclaimers."""
    return render_template('about.html')
