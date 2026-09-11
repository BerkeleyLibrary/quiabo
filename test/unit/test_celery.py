from quiabo import celery
from celery import Celery as CeleryApp

def test_celery_init_app(app):
    with app.app_context():
        celery_app = celery.celery_init_app(app)
        assert isinstance(celery_app, CeleryApp)
