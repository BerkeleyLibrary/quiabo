import os

from flask import Flask

from quiabo import health, root
from quiabo.celery import celery_init_app

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_prefixed_env(prefix="QUIABO")

    app.register_blueprint(root.bp)
    app.register_blueprint(health.bp)

    return app

app = create_app()
celery_app = celery_init_app(app)

