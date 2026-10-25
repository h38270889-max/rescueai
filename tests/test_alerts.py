from extensions import db
from app.models.alert import EmergencyAlert
from app.models.notification import UserNotification
from app.services.notification_service import dispatch_emergency_alert

def test_broadcast_alert_to_all_consented_users(client, app, test_users):
    """Admin alert broadcast generates in-app notifications for all consented users."""
    client.post('/auth/login', data={
        'email': 'admin.test@resqai.org',
        'password': 'AdminPass123'
    })

    response = client.post('/admin/alerts/create', data={
        'title': 'Severe Cyclone Warning Alpha',
        'category': 'other',
        'urgency': 'Critical',
        'target_audience': 'all',
        'target_region': '',
        'message': 'Severe cyclone warning issued. Relocate to designated shelters.'
    }, follow_redirects=True)

    assert response.status_code == 200
    with app.app_context():
        alert = EmergencyAlert.query.filter_by(title='Severe Cyclone Warning Alpha').first()
        assert alert is not None
        
        # Check notifications generated: admin + responder + citizen1 + citizen2 = 4 users
        notifs = UserNotification.query.filter_by(alert_id=alert.id).all()
        assert len(notifs) >= 4


def test_regional_targeted_alert(app, test_users):
    """Targeted regional alert delivers only to users in the specified region."""
    with app.app_context():
        # Create regional alert targeting 'Delhi NCR'
        alert = EmergencyAlert(
            created_by_user_id=test_users['admin_id'],
            title='Delhi Regional Smog & Fire Advisory',
            category='fire',
            urgency='High',
            target_audience='region',
            target_region='Delhi NCR',
            message='Severe air hazard advisory in Delhi NCR.'
        )
        db.session.add(alert)
        db.session.flush()

        result = dispatch_emergency_alert(alert, current_user_id=test_users['admin_id'])
        assert result['success'] is True
        
        # Only Citizen 2 is in 'Delhi NCR'
        delhi_notifs = UserNotification.query.filter_by(alert_id=alert.id).all()
        assert len(delhi_notifs) == 1
        assert delhi_notifs[0].user_id == test_users['citizen2_id']


def test_notification_read_unread_workflow(client, app, test_users):
    """Verify notification read status can be updated."""
    with app.app_context():
        notif = UserNotification(
            user_id=test_users['citizen1_id'],
            title='Test Alert Notice',
            message='This is an emergency test notification',
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
        notif_id = notif.id

    client.post('/auth/login', data={
        'email': 'citizen1@example.com',
        'password': 'CitizenPass123'
    })

    # Mark as read
    res = client.post(f'/notifications/{notif_id}/read', follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        updated = UserNotification.query.get(notif_id)
        assert updated.is_read is True
