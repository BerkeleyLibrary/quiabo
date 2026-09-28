"""Tests for the jobs endpoints."""
from unittest.mock import Mock


def test_create_job(client, tmp_path, monkeypatch):
    """POST /jobs returns an accepted response."""
    fake_result = Mock()
    fake_result.id = "12345"
    delay = Mock(return_value=fake_result)

    monkeypatch.setattr("quiabo.jobs.run_tesseract_job.delay", delay)

    filelist = tmp_path / "filelist.txt"
    filelist.touch()

    job = {
        "filelist": str(filelist),
        "languages": ["eng"],
        "output": "/srv/test/output.pdf",
    }

    response = client.post("/jobs", json=job)

    delay.assert_called_once_with(
        str(filelist),
        ["eng"],
        "/srv/test/output.pdf",
    )

    assert response.status_code == 202
    assert response.json == {
        "job_id": "12345",
        "status": "PENDING",
        "job_status": "/jobs/12345",
    }

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
    assert response.json["status"] == "ERROR"
    assert "output is required" in response.json["result"]
    assert "traceback" in response.json

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
    assert response.json["status"] == "ERROR"
    assert "languages must not be empty" in response.json["result"]
    assert "traceback" in response.json

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

def test_create_job_returns_500_when_queue_fails(client, tmp_path, monkeypatch):
    """POST /jobs returns 500 when queue fails."""
    filelist = tmp_path / "filelist.txt"
    filelist.touch()

    delay = Mock(side_effect=RuntimeError("queue unavailable"))
    monkeypatch.setattr("quiabo.jobs.run_tesseract_job.delay", delay)

    response = client.post("/jobs", json={
        "filelist": str(filelist),
        "languages": ["eng"],
        "output": "/srv/test/output.pdf",
    })

    assert response.status_code == 500
    assert response.json["status"] == "ERROR"
    assert "queue unavailable" in response.json["result"]
    assert "traceback" in response.json

def test_create_job_requires_filelist_to_be_file(client, tmp_path):
    """POST /jobs returns 422 when filelist is not a file."""
    filelist = tmp_path / "filelist"
    filelist.mkdir()

    job = {
        "filelist": str(filelist),
        "languages": ["eng"],
        "output": "/srv/test/output.pdf",
    }

    response = client.post("/jobs", json=job)

    assert response.status_code == 422
    assert response.json["status"] == "ERROR"
    assert "does not exist or is not a file" in response.json["result"]
    assert "traceback" in response.json
