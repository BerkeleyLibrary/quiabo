import os

from flask import Flask

from quiabo import health, root
from quiabo.celery import celery_init_app

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        CELERY=dict(
            broker_url=REDIS_URL,
            result_backend=DATABASE_URL,
            task_default_queue="quiabo",
            task_ignore_result=False,
        ),
    )

    app.register_blueprint(root.bp)
    app.register_blueprint(health.bp)

    return app

app = create_app()
celery_app = celery_init_app(app)

