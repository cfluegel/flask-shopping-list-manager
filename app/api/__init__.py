from flask import Blueprint

api_bp = Blueprint('api', __name__, template_folder='templates', static_folder='static')

# Import legacy routes (for backwards compatibility)
from . import routes

# Register v1 API blueprint
from .v1 import v1_bp
api_bp.register_blueprint(v1_bp, url_prefix='/v1')
