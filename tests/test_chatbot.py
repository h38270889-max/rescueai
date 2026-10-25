import json

def test_chatbot_fallback_mode_without_api_key(client):
    """Verify chatbot returns immediate deterministic guidance even when offline/no API key."""
    response = client.post('/api/chat', json={
        'message': 'There is a severe fire in my apartment building and stairs have smoke.',
        'language': 'en'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['category'] == 'fire'
    assert data['urgency'] in ('Critical', 'High')
    assert data['is_fallback'] is True
    assert '112' in data['reply'] or '101' in data['reply']


def test_chatbot_multilingual_query_handling(client):
    """Verify chatbot understands Hindi/Marathi emergency keywords in fallback mode."""
    response = client.post('/api/chat', json={
        'message': 'बाढ़ का पानी घर में घुस गया है और हम छत पर फंसे हैं।',
        'language': 'hi'
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['category'] == 'flood'
    assert '112' in data['reply']


def test_chatbot_history_and_clear(client):
    """Verify conversation history retrieval and clear endpoints."""
    # Send message with explicit session ID
    session_id = 'test-session-chat-999'
    client.post('/api/chat', json={
        'message': 'What is the emergency helpline for India?',
        'session_id': session_id,
        'language': 'en'
    })

    # Retrieve history
    hist_res = client.get(f'/api/chat/history?session_id={session_id}')
    assert hist_res.status_code == 200
    hist_data = hist_res.get_json()
    assert len(hist_data['messages']) >= 2  # 1 user + 1 assistant

    # Clear conversation
    clear_res = client.post('/api/chat/clear', json={'session_id': session_id})
    assert clear_res.status_code == 200

    # Retrieve history again (must be empty)
    hist_after = client.get(f'/api/chat/history?session_id={session_id}')
    assert len(hist_after.get_json()['messages']) == 0


def test_chatbot_csrf_exemption_with_active_csrf(app):
    """Verify JSON chat API functions without 400 error when CSRF protection is strictly active."""
    app.config['WTF_CSRF_ENABLED'] = True
    test_client = app.test_client()
    response = test_client.post('/api/chat', json={
        'message': 'Chemical leak in factory',
        'language': 'en'
    })
    assert response.status_code == 200
    assert response.get_json()['success'] is True

