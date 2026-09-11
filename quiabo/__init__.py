import os

from flask import Flask

from quiabo.celery import celery_init_app

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL")

app = Flask(__name__)

app.config.from_mapping(
    CELERY=dict(
        broker_url=REDIS_URL,
        result_backend=DATABASE_URL,
        task_default_queue="quiabo",
        task_ignore_result=False,
    ),
)

celery_app = celery_init_app(app)

@app.route('/')
def index():
    return "Goodbye Doggy!"


@app.route('/health')
def health():
    return {
        "default": {
            "message": "Application is running",
            "success": True
        }
    }
