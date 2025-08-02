def test_register(test_client, user_service, username, password):
    res = test_client.post('/user/register', json={'username': username, 'password': password})
    assert res.status_code == 200, res.json()
