"""Tests for the jobs endpoints."""


def test_create_job(client, tmp_path):
    """POST /jobs returns and accepted response."""
    filelist = tmp_path / "filelist.txt"
    filelist.touch()

    job = {
        "filelist": str(filelist),
        "languages": ["eng"],
        "output": "/srv/test/output.pdf",
    }

    response = client.post("/jobs", json=job)

    assert response.status_code == 202

def test_create_job_requires_filelist(client):
    """POST /jobs returns 422 when filelist is missing."""
    job = {
        "languages": ["eng"],
        "output": "/srv/test/output.pdf",
    }

    response = client.post("/jobs", json=job)

    assert response.status_code == 422
    assert response.json["status"] == "ERROR"
    assert "filelist is required" in response.json["result"]
    assert "traceback" in response.json

def test_create_job_requires_existing_filelist(client):
    """POST /jobs returns 422 when a filelist does not exist."""
    job = {
        "filelist": "/srv/test/does-not-exist.txt",
        "languages": ["eng"],
        "output": "/srv/test/output.pdf",
    }

    response = client.post("/jobs", json=job)

    assert response.status_code == 422
    assert response.json["status"] == "ERROR"
    assert "does not exist" in response.json["result"]
    assert "traceback" in response.json

def test_create_job_requires_languages(client, tmp_path):
    """POST /jobs returns 422 when languages is missing."""
    filelist = tmp_path / "filelist.txt"
    filelist.touch()

    job = {
        "filelist": str(filelist),
        "output": "/srv/test/output.pdf",
    }

    response = client.post("/jobs", json=job)

    assert response.status_code == 422
    assert response.json["status"] == "ERROR"
    assert "languages is required" in response.json["result"]
    assert "traceback" in response.json

def test_create_job_requires_output(client, tmp_path):
    """POST /jobs returns 422 when output is missing."""
    filelist = tmp_path / "filelist.txt"
    filelist.touch()

    job = {
        "filelist": str(filelist),
        "languages": ["eng"],
    }

    response = client.post("/jobs", json=job)

    assert response.status_code == 422

def test_create_job_requires_languages_not_empty(client, tmp_path):
    """POST /jobs returns 422 when languages is empty."""
    filelist = tmp_path / "filelist.txt"
    filelist.touch()

    job = {
        "filelist": str(filelist),
        "languages": [],
        "output": "/srv/test/output.pdf",
    }

    response = client.post("/jobs", json=job)

    assert response.status_code == 422

def test_create_job_requires_languages_list(client, tmp_path):
    """POST /jobs returns 422 when languages is not a list."""
    filelist = tmp_path / "filelist.txt"
    filelist.touch()

    job = {
        "filelist": str(filelist),
        "languages": "eng",
        "output": "/srv/test/output.pdf",
    }

    response = client.post("/jobs", json=job)

    assert response.status_code == 422
    assert response.json["status"] == "ERROR"
    assert "languages must be a list" in response.json["result"]
    assert "traceback" in response.json
