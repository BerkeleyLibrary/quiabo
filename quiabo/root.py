from flask import Blueprint

bp = Blueprint("root", __name__, url_prefix="")

@bp.route("/")
def index() -> str:
    """Default root endpoint."""
    return "<h1>Goodbye Doggy!<h1>"
