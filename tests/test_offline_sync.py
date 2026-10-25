"""
Unit and integration tests for ResQAI Offline PWA Synchronization and Idempotency.
Tests offline report submission, batch replay, and duplicate UUID suppression.
"""

import uuid
from extensions import db
from app.models.incident import EmergencyReport

def test_offline_sync_batch_submission(client, app):
    idempotency_key = str(uuid.uuid4())
    payload = {
        'reports': [
            {
                'idempotency_key': idempotency_key,
                'category': 'Flood / Waterlogging',
                'description': 'Water levels rising rapidly near metro station',
                'original_language': 'en',
                'latitude': 19.0760,
                'longitude': 72.8777,
                'affected_count': 5
            }
        ]
    }

    # 1. First sync submission
    res = client.post('/api/offline-sync', json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'success'
    assert len(data['results']) == 1
    assert data['results'][0]['status'] == 'synced'

    # Verify report in database
    with app.app_context():
        rep = EmergencyReport.query.filter_by(idempotency_key=idempotency_key).first()
        assert rep is not None
        assert rep.category == 'Flood / Waterlogging'

    # 2. Replay same sync submission with same idempotency key
    res2 = client.post('/api/offline-sync', json=payload)
    assert res2.status_code == 200
    data2 = res2.get_json()
    assert data2['results'][0]['status'] == 'already_synced'

    # Verify only ONE report exists in database
    with app.app_context():
        count = EmergencyReport.query.filter_by(idempotency_key=idempotency_key).count()
        assert count == 1

def test_network_ping(client):
    res = client.get('/api/ping')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'online'
    assert data['service'] == 'ResQAI Emergency Core'
