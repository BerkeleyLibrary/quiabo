"""Test route/controller for healthchecks."""

def test_health_default_route(client):
    """Test default healthcheck route."""
    response = client.get("/health")
    assert response.json["default"]["success"] is True
