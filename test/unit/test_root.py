"""Test application root route/controller."""

def test_root_route(client):
    """Ensure the expected message gets returned from the application root."""
    response = client.get("/")
    assert b"Goodbye Doggy!" in response.data
