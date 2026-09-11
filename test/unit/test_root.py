def test_root_route(client):
    response = client.get("/")
    assert b"Goodbye Doggy!" in response.data
