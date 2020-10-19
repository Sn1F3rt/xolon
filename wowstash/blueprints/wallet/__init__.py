from flask import Blueprint

wallet_bp = Blueprint("wallet", __name__)

from . import routes
