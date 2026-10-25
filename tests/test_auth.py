from datetime import datetime, timedelta, timezone
from app.models.user import User, PasswordResetToken

def test_register_creates_account(client, app):
    """Verify new user registration creates database record with hashed password."""
    response = client.post('/auth/register', data={
        'full_name': 'Test New User',
        'email': 'newuser@example.com',
        'password': 'SecurePassword123',
        'confirm_password': 'SecurePassword123',
        'preferred_language': 'en',
        'region': 'Mumbai Metro',
        'consent_emergency_notifications': 'y'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(email='newuser@example.com').first()
        assert user is not None
        assert user.full_name == 'Test New User'
        assert user.role == 'user'
        assert user.check_password('SecurePassword123') is True
        assert user.password_hash != 'SecurePassword123'  # Must be hashed


def test_duplicate_email_registration_rejected(client, test_users):
    """Verify registration fails if email already exists in database."""
    response = client.post('/auth/register', data={
        'full_name': 'Duplicate User',
        'email': 'citizen1@example.com',
        'password': 'SomePassword123',
        'confirm_password': 'SomePassword123',
        'preferred_language': 'en',
        'consent_emergency_notifications': 'y'
    })

    assert response.status_code == 200
    assert b"already registered" in response.data or b"is-invalid" in response.data


def test_login_valid_credentials(client, test_users):
    """Verify successful login for valid credentials."""
    response = client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'CitizenPass123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome back" in response.data or b"Dashboard" in response.data


def test_login_invalid_credentials(client, test_users):
    """Verify login failure on incorrect password."""
    response = client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'WrongPassword123'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_logout(client, test_users):
    """Verify logout terminates user session."""
    client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'CitizenPass123'
    })

    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b"signed out" in response.data or b"Sign In" in response.data


def test_password_reset_token_expiration(app, test_users):
    """Verify single-use token validity and expiration logic."""
    with app.app_context():
        user = User.query.filter_by(email='citizen1@example.com').first()
        
        # Valid token
        valid_token = PasswordResetToken(
            user_id=user.id,
            token="valid-token-12345",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used=False
        )
        assert valid_token.is_valid() is True

        # Expired token
        expired_token = PasswordResetToken(
            user_id=user.id,
            token="expired-token-12345",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            used=False
        )
        assert expired_token.is_valid() is False

        # Used token
        used_token = PasswordResetToken(
            user_id=user.id,
            token="used-token-12345",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used=True
        )
        assert used_token.is_valid() is False
