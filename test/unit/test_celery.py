"""Test Celery app initialization."""

from celery import Celery as CeleryApp
from quiabo import celery

def test_celery_init_app(app):
    """Ensure a test Celery application is instantiated."""
    with app.app_context():
        celery_app = celery.celery_init_app(app)
        assert isinstance(celery_app, CeleryApp)
