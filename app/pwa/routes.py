"""
PWA Blueprint Routes.

Serves the SPA shell, manifest, and service worker.
"""

from flask import render_template, send_from_directory, current_app
from . import pwa_bp


@pwa_bp.route('/')
@pwa_bp.route('/<path:path>')
def index(path=None):
    """Serve the SPA shell for all PWA routes."""
    return render_template('pwa.html')


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
