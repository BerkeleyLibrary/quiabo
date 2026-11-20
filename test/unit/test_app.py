"""Tests for Flask application configuration."""

from quiabo import create_app


def test_default_ocr_retry_config(monkeypatch):
    """OCR retry settings have sensible defaults."""
    monkeypatch.delenv("QUIABO_OCR_MAX_RETRIES", raising=False)
    monkeypatch.delenv("QUIABO_OCR_RETRY_BACKOFF", raising=False)

    app = create_app()

    assert app.config["OCR_MAX_RETRIES"] == 3
    assert app.config["OCR_RETRY_BACKOFF"] == 30


def test_ocr_retry_config_from_environment(monkeypatch):
    """Environment variables override OCR retry defaults."""
    monkeypatch.setenv("QUIABO_OCR_MAX_RETRIES", "5")
    monkeypatch.setenv("QUIABO_OCR_RETRY_BACKOFF", "60")

    app = create_app()

    assert app.config["OCR_MAX_RETRIES"] == 5
    assert app.config["OCR_RETRY_BACKOFF"] == 60
