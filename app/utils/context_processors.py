from flask import session, current_app
from flask_login import current_user
from app.services.translation_service import translate_ui
from app.models.notification import UserNotification
from app.models.alert import EmergencyAlert

def register_context_processors(app):
    """Register global Jinja template helpers and variables."""

    @app.context_processor
    def inject_global_template_context():
        # Determine active language
        lang = session.get('lang')
        if not lang and current_user.is_authenticated:
            lang = current_user.preferred_language
        if not lang:
            lang = app.config.get('DEFAULT_LANGUAGE', 'en')

        supported_languages = app.config.get('SUPPORTED_LANGUAGES', {})
        lang_info = supported_languages.get(lang, {'name': 'English', 'native': 'English', 'dir': 'ltr'})
        text_dir = lang_info.get('dir', 'ltr')

        # Unread notifications count
        unread_count = 0
        if current_user.is_authenticated:
            try:
                unread_count = UserNotification.query.filter_by(
                    user_id=current_user.id, is_read=False
                ).count()
            except Exception:
                unread_count = 0

        # Active public emergency alerts
        active_alerts_count = 0
        try:
            active_alerts_count = EmergencyAlert.query.filter_by(is_active=True).count()
        except Exception:
            active_alerts_count = 0

        def t(key, default=None):
            return translate_ui(key, lang, default)

        return {
            'current_language': lang,
            'current_lang_info': lang_info,
            'text_dir': text_dir,
            'supported_languages': supported_languages,
            'unread_notifications_count': unread_count,
            'active_alerts_count': active_alerts_count,
            'emergency_directory': app.config.get('EMERGENCY_DIRECTORY', {}),
            't': t
        }
