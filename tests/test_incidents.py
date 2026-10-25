from extensions import db
from app.models.incident import EmergencyReport, IncidentStatusHistory

def test_emergency_report_creation_generates_unique_id(client, app, test_users):
    """Verify filing emergency report generates unique incident_id and AI triage."""
    client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'CitizenPass123'
    })

    response = client.post('/incidents/report', data={
        'category': 'fire',
        'description': 'Heavy smoke and flames on 4th floor, cylinder blast suspected.',
        'original_language': 'en',
        'contact_name': 'Test Submitter',
        'contact_phone': '+91 99999 88888',
        'location_address': 'Sector 5, Industrial Area',
        'affected_count': 5,
        'consent': 'y'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        report = EmergencyReport.query.filter_by(contact_name='Test Submitter').first()
        assert report is not None
        assert report.incident_id.startswith('INC-')
        assert report.status == 'Submitted'
        assert report.ai_suggested_priority in ('Critical', 'High')
        assert report.is_high_risk is True


def test_user_can_view_own_report(client, app, test_users):
    """Citizen can open and view the tracking timeline of their own incident report."""
    with app.app_context():
        report = EmergencyReport(
            user_id=test_users['citizen1_id'],
            category='flood',
            description='Water rising near doorway',
            incident_id='INC-CITIZEN1-01',
            status='Submitted'
        )
        db.session.add(report)
        db.session.commit()

    client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'CitizenPass123'
    })

    response = client.get('/incidents/INC-CITIZEN1-01')
    assert response.status_code == 200
    assert b"INC-CITIZEN1-01" in response.data
    assert b"Water rising near doorway" in response.data


def test_responder_updates_incident_status(client, app, test_users):
    """Authorized responder claims and updates incident status."""
    with app.app_context():
        report = EmergencyReport(
            user_id=test_users['citizen1_id'],
            category='rescue_request',
            description='Boat needed for evacuation',
            incident_id='INC-RESCUE-01',
            status='Submitted'
        )
        db.session.add(report)
        db.session.commit()

    # Log in as responder
    client.post('/auth/login', data={
        'email': 'responder.test@resqai.org',
        'password': 'RespPass123'
    })

    # Post status update
    response = client.post('/responder/incidents/INC-RESCUE-01', data={
        'status': 'In Progress',
        'notes': 'Rescue boat Alpha dispatched to coordinates.'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        updated = EmergencyReport.query.filter_by(incident_id='INC-RESCUE-01').first()
        assert updated.status == 'In Progress'
        assert 'Rescue boat Alpha' in updated.responder_notes


def test_admin_csv_export(client, app, test_users):
    """Verify administrator CSV export endpoint streams proper CSV data."""
    client.post('/auth/login', data={
        'email': 'admin.test@resqai.org',
        'password': 'AdminPass123'
    })

    response = client.get('/admin/incidents/export/csv')
    assert response.status_code == 200
    assert 'text/csv' in response.headers.get('Content-Type', '')
    assert b'Incident ID,Category,AI Priority' in response.data
