import pytest
from app import create_app
from extensions import db
from app.models.user import User

@pytest.fixture
def app():
    """Create test application with in-memory SQLite and disabled CSRF."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Test client for HTTP requests."""
    return app.test_client()

@pytest.fixture
def test_users(app):
    """Seed sample users with different roles."""
    with app.app_context():
        admin = User(
            full_name="Admin Test",
            email="admin.test@resqai.org",
            role="admin",
            region="Mumbai Metro",
            consent_emergency_notifications=True
        )
        admin.set_password("AdminPass123")

        responder = User(
            full_name="Responder Test",
            email="responder.test@resqai.org",
            role="responder",
            region="Mumbai Metro",
            consent_emergency_notifications=True
        )
        responder.set_password("RespPass123")

        citizen1 = User(
            full_name="Citizen One",
            email="citizen1@example.com",
            role="user",
            region="Mumbai Metro",
            consent_emergency_notifications=True
        )
        citizen1.set_password("CitizenPass123")

        citizen2 = User(
            full_name="Citizen Two",
            email="citizen2@example.com",
            role="user",
            region="Delhi NCR",
            consent_emergency_notifications=True
        )
        citizen2.set_password("CitizenPass123")

        db.session.add_all([admin, responder, citizen1, citizen2])
        db.session.commit()

        return {
            'admin_id': admin.id,
            'responder_id': responder.id,
            'citizen1_id': citizen1.id,
            'citizen2_id': citizen2.id
        }
