from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.dashboard import dashboard_bp
from app.routes.incidents import incidents_bp
from app.routes.alerts import alerts_bp
from app.routes.chatbot import chatbot_bp
from app.routes.admin import admin_bp
from app.routes.responder import responder_bp
from app.routes.api import api_bp
from app.routes.map import map_bp
from app.routes.family import family_bp

__all__ = [
    'main_bp',
    'auth_bp',
    'dashboard_bp',
    'incidents_bp',
    'alerts_bp',
    'chatbot_bp',
    'admin_bp',
    'responder_bp',
    'api_bp',
    'map_bp',
    'family_bp'
]
