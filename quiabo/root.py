"""
Route/controller for the application root.
"""

from flask import Blueprint, render_template

bp = Blueprint("root", __name__, url_prefix="")

@bp.route("/")
def index() -> str:
    """Default root endpoint."""
    return render_template('root/index.html')
