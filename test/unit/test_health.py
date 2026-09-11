def test_health_route(client):
    response = client.get("/health")
    assert response.json["default"]["success"] == True
