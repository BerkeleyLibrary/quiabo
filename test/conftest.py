# pylint: disable=W0621

"""pytest setup and fixtures for quiabo."""

import pytest
from flask import Flask
from quiabo import app as flask_app


@pytest.fixture()
def app() -> Flask:
    """Create a configured instance of the Flask application for testing.

    :return: The Flask application.
    :rtype: Flask
    """
    app = flask_app
    app.config.update(
        {
            "TESTING": True,
        }
    )

    return app


@pytest.fixture()
def client(app: Flask):
    """
    Given a configured application, return a test HTTP client for checking
    routes/controllers.
    """
    return app.test_client()


@pytest.fixture()
def runner(app: Flask):
    """
    Given a configured application, return a test runner for running CLI
    commands.
    """
    return app.test_cli_runner()
