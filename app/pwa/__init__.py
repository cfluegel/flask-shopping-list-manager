from flask import Blueprint

pwa_bp = Blueprint('pwa', __name__, template_folder='templates')

from . import routes
