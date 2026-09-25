"""Code to initialize the Celery application based on an existing Flask app."""

from celery import Celery, Task
from flask import Flask

def celery_init_app(app: Flask) -> Celery:
    """
    Given a properly configured Flask application, return a configured
    Celery app.
    """
    class FlaskTask(Task):
        """
        Class used to provide access to Celery decoratorss.

        :see: https://flask.palletsprojects.com/en/stable/patterns/celery/
        """
        def __call__(self, *args: object, **kwargs: object) -> object:
            """
            Create a callable instance since Celery otherwise does not
            have direct access to the Flask application context.

            :param args: positional arguments to get passed in the call
            :type args: object
            :param kwargs: keyword arguments to get passed in the call
            :type kwargs: object
            :return: The output of the task to be run.
            :rtype: Object
            """
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    celery_app.autodiscover_tasks(["quiabo"], force=True)
    app.extensions["celery"] = celery_app
    return celery_app
