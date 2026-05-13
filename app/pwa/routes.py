"""
PWA Blueprint Routes.

Serves the SPA shell, manifest, and service worker.
"""

from flask import render_template, send_from_directory, current_app
from flask_jwt_extended import create_access_token, create_refresh_token

from . import pwa_bp
from ..models import User


@pwa_bp.route('/')
@pwa_bp.route('/<path:path>')
def index(path=None):
    """Serve the SPA shell for all PWA routes."""
    if current_app.config.get('AUTO_LOGIN', False):
        admin = User.query.filter_by(username='admin').first()
        if admin is not None:
            access_token = create_access_token(identity=str(admin.id))
            refresh_token = create_refresh_token(identity=str(admin.id))
            return render_template(
                'pwa.html',
                auto_login=True,
                access_token=access_token,
                refresh_token=refresh_token,
                user={
                    'id': admin.id,
                    'username': admin.username,
                    'email': admin.email,
                    'is_admin': admin.is_admin,
                },
            )
    return render_template('pwa.html', auto_login=False)


@pwa_bp.route('/manifest.json')
def manifest():
    """Serve the PWA manifest."""
    return send_from_directory(
        current_app.static_folder, 'pwa/manifest.json',
        mimetype='application/manifest+json'
    )


@pwa_bp.route('/sw.js')
def service_worker():
    """Serve the service worker at PWA scope root."""
    return send_from_directory(
        current_app.static_folder, 'pwa/sw.js',
        mimetype='application/javascript'
    )
