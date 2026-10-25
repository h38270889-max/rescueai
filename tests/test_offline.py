from extensions import db
from app.models.incident import EmergencyReport

def test_offline_sync_creates_report(client, app):
    """Verify offline report synced via API is recorded in database."""
    idempotency_key = "idemp-test-offline-uuid-1111"
    response = client.post('/api/sync/report', json={
        'idempotency_key': idempotency_key,
        'category': 'flood',
        'description': 'Water entering ground floor rooms, 3 elderly people trapped.',
        'original_language': 'en',
        'contact_name': 'Offline Submitter',
        'affected_count': 3
    })

    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'synced'
    assert data['is_duplicate'] is False
    assert data['incident_id'].startswith('INC-')

    with app.app_context():
        report = EmergencyReport.query.filter_by(idempotency_key=idempotency_key).first()
        assert report is not None
        assert report.contact_name == 'Offline Submitter'


def test_offline_sync_idempotency_deduplication(client, app):
    """Verify resending same idempotency key prevents duplicate incident creation."""
    idempotency_key = "idemp-test-offline-uuid-2222"
    
    # First sync attempt
    res1 = client.post('/api/sync/report', json={
        'idempotency_key': idempotency_key,
        'category': 'medical',
        'description': 'Patient fractured arm during earthquake evacuation.',
        'original_language': 'en'
    })
    assert res1.status_code == 201
    inc_id = res1.get_json()['incident_id']

    # Second sync attempt with SAME idempotency key (e.g. network flap/retry)
    res2 = client.post('/api/sync/report', json={
        'idempotency_key': idempotency_key,
        'category': 'medical',
        'description': 'Patient fractured arm during earthquake evacuation.',
        'original_language': 'en'
    })
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2['status'] == 'synced'
    assert data2['is_duplicate'] is True
    assert data2['incident_id'] == inc_id

    # Verify exactly one record exists in database
    with app.app_context():
        count = EmergencyReport.query.filter_by(idempotency_key=idempotency_key).count()
        assert count == 1


def test_offline_guide_page_loads(client):
    """Verify the offline emergency survival handbook loads with 200 OK."""
    response = client.get('/offline-guide')
    assert response.status_code == 200
    assert b"Emergency Survival Handbook" in response.data


def test_network_ping_endpoint(client):
    """Verify connectivity check API returns online status."""
    response = client.get('/api/ping')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'online'
