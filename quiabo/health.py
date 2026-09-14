"""Route/controller for a healthcheck endpoint. Requires significant expansion."""

from flask import Blueprint

bp = Blueprint("health", __name__, url_prefix="/health")

@bp.route("")
def default() -> dict[str, dict[str, str|bool]]:
    """
    Default healthcheck endpoint. Because of Flask magic, this gets returned
    to the client as a JSON object.

    Healthchecks are expected to contain a key for the healthcheck, the
    message, and a bool for whether the check is successful.

    :return: The output of the healthcheck. Currently only confirms that
             the application is running and can serve the route.
    :rtype: dict[str, dict[str, str|bool]]
    """
    return {
        "default": {
            "message": "Application is running",
            "success": True
        }
    }
