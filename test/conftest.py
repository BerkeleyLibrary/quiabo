# pylint: disable=W0621

"""pytest setup and fixtures for quiabo."""

import pytest
from flask import Flask
from quiabo import app as flask_app

@pytest.fixture()
def app():
    """Create a configured instance of the Flask application for testing.

    :return: The Flask application.
    :rtype: flask.Flask
    """
    app = flask_app
    app.config.update({
        "TESTING": True,
    })

    yield app

    # clean up / reset resources here


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
