"""
API v1 Blueprint.

This blueprint contains all versioned API endpoints for mobile apps.
"""

from flask import Blueprint

v1_bp = Blueprint('api_v1', __name__)

# Import routes to register them with the blueprint
from . import auth, users, lists, items, shared, admin
