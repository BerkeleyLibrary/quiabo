"""Flask application intialization functions."""

from flask import Flask
from flask.logging import default_handler

from quiabo import health, jobs, root
from quiabo.celery import celery_init_app
from quiabo.logging import JsonFormatter


def create_app() -> Flask:
    """
    Creates the Flask application.

    :rtype: Flask
    """
    flask_app = Flask(__name__)

    default_handler.setFormatter(JsonFormatter())

    flask_app.config.from_prefixed_env(prefix="QUIABO")

    flask_app.register_blueprint(root.bp)
    flask_app.register_blueprint(health.bp)
    flask_app.register_blueprint(jobs.bp)

    return flask_app


app = create_app()
celery_app = celery_init_app(app)
