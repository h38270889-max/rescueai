"""
Unit and integration tests for ResQAI Role-Based Access Control (RBAC).
Validates strict route authorization boundaries between citizens, responders, and administrators.
"""

def test_unauthenticated_protected_routes_redirect_to_login(client):
    protected_urls = [
        '/dashboard',
        '/incidents/my-reports',
        '/admin/',
        '/admin/incidents',
        '/admin/duplicates',
        '/responder/',
        '/family/'
    ]
    for url in protected_urls:
        res = client.get(url, follow_redirects=False)
        assert res.status_code in (302, 401)
        assert '/auth/login' in res.headers.get('Location', '')

def test_citizen_forbidden_from_admin_and_responder(client, test_users):
    # Log in as citizen
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_users['citizen1_id'])
        sess['_fresh'] = True

    # Attempting to access admin portal returns 403 Forbidden
    res_admin = client.get('/admin/')
    assert res_admin.status_code == 403

    # Attempting to access duplicate review console returns 403 Forbidden
    res_dup = client.get('/admin/duplicates')
    assert res_dup.status_code == 403

    # Attempting to access responder desk returns 403 Forbidden
    res_resp = client.get('/responder/')
    assert res_resp.status_code == 403

def test_responder_access_boundaries(client, test_users):
    # Log in as responder
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_users['responder_id'])
        sess['_fresh'] = True

    # Responder can access responder dashboard
    res_resp = client.get('/responder/')
    assert res_resp.status_code == 200

    # Responder CANNOT access admin dashboard
    res_admin = client.get('/admin/')
    assert res_admin.status_code == 403

def test_admin_has_full_access(client, test_users):
    # Log in as admin
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_users['admin_id'])
        sess['_fresh'] = True

    # Admin accesses admin portal
    res_admin = client.get('/admin/')
    assert res_admin.status_code == 200

    # Admin accesses duplicate review portal
    res_dup = client.get('/admin/duplicates')
    assert res_dup.status_code == 200

    # Admin also has responder console privileges
    res_resp = client.get('/responder/')
    assert res_resp.status_code == 200
