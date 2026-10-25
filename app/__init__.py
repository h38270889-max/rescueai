import os
from flask import Flask, render_template
from config import config_by_name
from extensions import db, login_manager, csrf
from app.models.user import User
from app.utils.context_processors import register_context_processors

def create_app(config_name='default'):
    """Application Factory for ResQAI."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Load Configuration
    config_obj = config_by_name.get(config_name, config_by_name['default'])
    app.config.from_object(config_obj)

    # Ensure Upload and Instance folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Global Context Processors (Translations, Badges, Direction)
    register_context_processors(app)

    # Register Blueprints
    from app.routes import (
        main_bp,
        auth_bp,
        dashboard_bp,
        incidents_bp,
        alerts_bp,
        chatbot_bp,
        admin_bp,
        responder_bp,
        api_bp,
        map_bp,
        family_bp
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(incidents_bp, url_prefix='/incidents')
    app.register_blueprint(alerts_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(responder_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(family_bp)

    # Custom Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Auto-create tables in development
    with app.app_context():
        db.create_all()

    return app
