from extensions import db
from app.models.incident import EmergencyReport

def test_unauthenticated_protected_routes(client):
    """Verify guests cannot access dashboard, admin, or responder pages."""
    assert client.get('/dashboard').status_code in (302, 401)
    assert client.get('/admin/').status_code in (302, 401)
    assert client.get('/responder/').status_code in (302, 401)


def test_citizen_cannot_access_admin_portal(client, test_users):
    """Ordinary citizen attempting to access admin route receives 403 Forbidden."""
    client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'CitizenPass123'
    })

    response = client.get('/admin/')
    assert response.status_code == 403


def test_citizen_cannot_access_responder_desk(client, test_users):
    """Ordinary citizen attempting to access responder desk receives 403 Forbidden."""
    client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'CitizenPass123'
    })

    response = client.get('/responder/')
    assert response.status_code == 403


def test_responder_can_access_responder_desk_but_not_admin(client, test_users):
    """Authorized responder can access responder desk, but is denied admin console."""
    client.post('/auth/login', data={
        'email': 'responder.test@resqai.org',
        'password': 'RespPass123'
    })

    assert client.get('/responder/').status_code == 200
    assert client.get('/admin/').status_code == 403


def test_admin_can_access_both_consoles(client, test_users):
    """Admin has full authorization across both admin and responder consoles."""
    client.post('/auth/login', data={
        'email': 'admin.test@resqai.org',
        'password': 'AdminPass123'
    })

    assert client.get('/admin/').status_code == 200
    assert client.get('/responder/').status_code == 200


def test_citizen_cannot_view_another_citizens_private_report(client, app, test_users):
    """Verify privacy boundary: User A cannot open User B's report details."""
    with app.app_context():
        report = EmergencyReport(
            user_id=test_users['citizen2_id'],
            category='medical',
            description='Private medical issue for citizen 2',
            incident_id='INC-PRIVATE-TEST-01',
            status='Submitted'
        )
        db.session.add(report)
        db.session.commit()

    # Log in as Citizen 1
    client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'CitizenPass123'
    })

    # Attempt to open Citizen 2's report
    response = client.get('/incidents/INC-PRIVATE-TEST-01')
    assert response.status_code == 403
