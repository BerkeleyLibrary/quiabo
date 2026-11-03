"""Test Celery app initialization."""

import logging
from unittest.mock import Mock

from celery import Celery as CeleryApp

from quiabo import celery
from quiabo.logging import JsonFormatter


def test_celery_init_app(app):
    """Ensure a test Celery application is instantiated."""
    with app.app_context():
        celery_app = celery.celery_init_app(app)
        assert isinstance(celery_app, CeleryApp)


def test_configure_json_logging():
    """Verify that Celery log handlers use the JSON formatter."""
    handler = logging.StreamHandler()
    logger = Mock()
    logger.handlers = [handler]

    celery.configure_json_logging(logger=logger)

    assert isinstance(handler.formatter, JsonFormatter)


def test_configure_json_logging_without_logger():
    """Verify that a missing logger is handled gracefully."""
    celery.configure_json_logging(logger=None)
