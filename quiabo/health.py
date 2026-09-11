from flask import Blueprint

bp = Blueprint("health", __name__, url_prefix="/health")

@bp.route("")
def default() -> dict[str, dict[str, str|bool]]:
    """Default healthcheck endpoint."""
    return {
        "default": {
            "message": "Application is running",
            "success": True
        }
    }
