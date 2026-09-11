def test_root_route(client):
    response = client.get("/")
    assert b"Goodbye Doggy!" in response.data


def test_health_route(client):
    response = client.get("/health")
    assert response.json["default"]["success"] == True
