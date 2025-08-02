from auth.api_errors import ApiErrors


def test_login_no_auth_raises_422(test_client):
    response = test_client.post('/auth/login')
    assert response.status_code == 422, response.json()


def test_login_wrong_auth_raises_401(test_client):
    response = test_client.post('/auth/login', data={'username': '_', 'password': '_'})
    assert response.status_code == 401, response.json()
    assert response.json() == ApiErrors.INVALID_LOGIN_OR_PASSWORD.json()


def test_login_with_auth_200(test_client, auth_in_db, password):
    response = test_client.post('/auth/login', data={'username': auth_in_db.username, 'password': password})
    assert response.status_code == 200, response.json()


def test_refresh_token_pair(test_client, refresh_token):
    response = test_client.post('/auth/refresh', cookies={'refresh_token': refresh_token})
    assert response.status_code == 200, response.json()


def test_refresh_no_refresh_token_raises_401(test_client):
    response = test_client.post('/auth/refresh')
    assert response.status_code == 401, response.json()
    assert response.json() == ApiErrors.REFRESH_TOKEN_REQUIRED.json()
