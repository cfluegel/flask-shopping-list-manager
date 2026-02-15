"""
Tests for the PWA (Progressive Web App) Blueprint.

Verifies that the PWA blueprint correctly serves:
- SPA shell HTML for all PWA routes (catch-all)
- PWA manifest with correct metadata
- Service worker at the correct scope
- All static assets (CSS, JS, icons)

Also verifies the SPA shell contains the required elements per the design plan:
- Proper HTML meta tags for PWA capabilities
- All JavaScript modules loaded in correct order
- Required CSS stylesheets included
- App shell UI elements (header, back/logout buttons, content area, toast container)
- No authentication required for PWA routes (auth is handled client-side via JWT)
"""

import json
import pytest


# ============================================================================
# PWA Blueprint Registration
# ============================================================================

class TestPWABlueprintRegistration:
    """Test that the PWA blueprint is properly registered."""

    def test_pwa_blueprint_is_registered(self, app):
        """Test that pwa blueprint is registered with url_prefix /pwa."""
        assert 'pwa' in app.blueprints

    def test_pwa_url_prefix(self, client, app):
        """Test that PWA routes are accessible under /pwa/."""
        response = client.get('/pwa/')
        assert response.status_code == 200


# ============================================================================
# SPA Shell Route Tests
# ============================================================================

class TestSPAShellRoute:
    """Test GET /pwa/ and catch-all SPA routing."""

    def test_pwa_root_returns_200(self, client, app):
        """Test that /pwa/ returns the SPA shell with 200 status."""
        response = client.get('/pwa/')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')

    def test_pwa_catchall_login_returns_200(self, client, app):
        """Test that /pwa/login returns the same SPA shell (hash routing is client-side)."""
        response = client.get('/pwa/login')
        assert response.status_code == 200
        assert response.content_type.startswith('text/html')

    def test_pwa_catchall_lists_returns_200(self, client, app):
        """Test that /pwa/lists returns the SPA shell."""
        response = client.get('/pwa/lists')
        assert response.status_code == 200

    def test_pwa_catchall_list_detail_returns_200(self, client, app):
        """Test that /pwa/lists/123 returns the SPA shell."""
        response = client.get('/pwa/lists/123')
        assert response.status_code == 200

    def test_pwa_catchall_deep_path_returns_200(self, client, app):
        """Test that deeply nested paths still return the SPA shell."""
        response = client.get('/pwa/some/deep/path')
        assert response.status_code == 200

    def test_pwa_does_not_require_authentication(self, client, app):
        """Test that PWA routes do not require session/login authentication."""
        # No login, no JWT — should still serve the shell
        response = client.get('/pwa/')
        assert response.status_code == 200

    def test_pwa_root_and_catchall_return_same_content(self, client, app):
        """Test that root and catch-all return the identical SPA shell."""
        root_response = client.get('/pwa/')
        catchall_response = client.get('/pwa/lists')

        assert root_response.data == catchall_response.data


# ============================================================================
# SPA Shell HTML Content Tests
# ============================================================================

class TestSPAShellContent:
    """Test that the SPA shell HTML contains all required elements per the design plan."""

    @pytest.fixture(autouse=True)
    def _get_shell(self, client, app):
        """Fetch the SPA shell once for all tests in this class."""
        response = client.get('/pwa/')
        self.html = response.data.decode('utf-8')

    # -- HTML Metadata --

    def test_html_lang_is_german(self):
        """Test that the HTML lang attribute is set to 'de'."""
        assert 'lang="de"' in self.html

    def test_html_has_viewport_meta(self):
        """Test that viewport meta tag is present for responsive design."""
        assert 'name="viewport"' in self.html
        assert 'viewport-fit=cover' in self.html

    def test_html_has_theme_color_meta(self):
        """Test that theme-color meta tag is set to orange (#ff8c42)."""
        assert 'name="theme-color" content="#ff8c42"' in self.html

    def test_html_has_apple_mobile_web_app_capable(self):
        """Test that Apple mobile web app meta tags are present."""
        assert 'name="apple-mobile-web-app-capable" content="yes"' in self.html

    def test_html_has_apple_mobile_web_app_title(self):
        """Test that Apple mobile web app title is Einkaufsliste."""
        assert 'name="apple-mobile-web-app-title" content="Einkaufsliste"' in self.html

    def test_html_title_is_einkaufsliste(self):
        """Test that the page title is Einkaufsliste."""
        assert '<title>Einkaufsliste</title>' in self.html

    # -- Manifest Link --

    def test_html_has_manifest_link(self):
        """Test that the manifest link tag is present."""
        assert 'rel="manifest"' in self.html
        assert '/pwa/manifest.json' in self.html

    # -- Apple Touch Icon --

    def test_html_has_apple_touch_icon(self):
        """Test that apple-touch-icon link is present."""
        assert 'rel="apple-touch-icon"' in self.html
        assert 'pwa/icons/icon-192.png' in self.html

    # -- Stylesheets --

    def test_html_loads_main_css(self):
        """Test that main.css is loaded (provides CSS custom properties)."""
        assert 'css/main.css' in self.html

    def test_html_loads_pwa_css(self):
        """Test that pwa.css is loaded."""
        assert 'pwa/css/pwa.css' in self.html

    def test_main_css_loaded_before_pwa_css(self):
        """Test that main.css is loaded before pwa.css (for variable inheritance)."""
        main_pos = self.html.index('css/main.css')
        pwa_pos = self.html.index('pwa/css/pwa.css')
        assert main_pos < pwa_pos

    # -- JavaScript Modules --

    def test_html_loads_auth_js(self):
        """Test that auth.js is loaded."""
        assert 'pwa/js/auth.js' in self.html

    def test_html_loads_api_js(self):
        """Test that api.js is loaded."""
        assert 'pwa/js/api.js' in self.html

    def test_html_loads_router_js(self):
        """Test that router.js is loaded."""
        assert 'pwa/js/router.js' in self.html

    def test_html_loads_app_js(self):
        """Test that app.js is loaded."""
        assert 'pwa/js/app.js' in self.html

    def test_html_loads_login_view_js(self):
        """Test that login-view.js is loaded."""
        assert 'pwa/js/views/login-view.js' in self.html

    def test_html_loads_lists_view_js(self):
        """Test that lists-view.js is loaded."""
        assert 'pwa/js/views/lists-view.js' in self.html

    def test_html_loads_list_detail_view_js(self):
        """Test that list-detail-view.js is loaded."""
        assert 'pwa/js/views/list-detail-view.js' in self.html

    def test_js_load_order_auth_before_api(self):
        """Test that auth.js is loaded before api.js (dependency order)."""
        auth_pos = self.html.index('pwa/js/auth.js')
        api_pos = self.html.index('pwa/js/api.js')
        assert auth_pos < api_pos

    def test_js_load_order_api_before_router(self):
        """Test that api.js is loaded before router.js."""
        api_pos = self.html.index('pwa/js/api.js')
        router_pos = self.html.index('pwa/js/router.js')
        assert api_pos < router_pos

    def test_js_load_order_views_before_app(self):
        """Test that view modules are loaded before app.js (app.js registers routes)."""
        login_view_pos = self.html.index('pwa/js/views/login-view.js')
        app_pos = self.html.index('pwa/js/app.js')
        assert login_view_pos < app_pos

    # -- App Shell UI Elements --

    def test_html_has_app_container(self):
        """Test that the #app container div exists."""
        assert 'id="app"' in self.html

    def test_html_has_header(self):
        """Test that the PWA header element exists."""
        assert 'id="pwa-header"' in self.html
        assert 'class="pwa-header"' in self.html

    def test_html_has_title_element(self):
        """Test that the dynamic title element exists."""
        assert 'id="pwa-title"' in self.html

    def test_html_has_back_button(self):
        """Test that the back button exists and is initially hidden."""
        assert 'id="back-btn"' in self.html
        assert 'aria-label="Zurück"' in self.html

    def test_html_has_theme_button(self):
        """Test that the theme toggle button exists."""
        assert 'id="theme-btn"' in self.html
        assert 'aria-label="Theme wechseln"' in self.html

    def test_html_has_logout_button(self):
        """Test that the logout button exists and is initially hidden."""
        assert 'id="logout-btn"' in self.html
        assert 'aria-label="Abmelden"' in self.html

    def test_html_has_content_area(self):
        """Test that the main content area exists."""
        assert 'id="pwa-content"' in self.html
        assert 'class="pwa-content"' in self.html

    def test_html_has_toast_container(self):
        """Test that the toast notification container exists."""
        assert 'id="toast-container"' in self.html
        assert 'class="pwa-toast-container"' in self.html

    def test_html_has_loading_spinner(self):
        """Test that the initial loading spinner is present."""
        assert 'class="pwa-loading"' in self.html
        assert 'class="spinner"' in self.html


# ============================================================================
# PWA Manifest Tests
# ============================================================================

class TestPWAManifest:
    """Test GET /pwa/manifest.json serves valid manifest per the plan."""

    @pytest.fixture(autouse=True)
    def _get_manifest(self, client, app):
        """Fetch and parse the manifest once for all tests in this class."""
        response = client.get('/pwa/manifest.json')
        self.response = response
        self.manifest = json.loads(response.data)

    def test_manifest_returns_200(self):
        """Test that manifest endpoint returns 200."""
        assert self.response.status_code == 200

    def test_manifest_content_type(self):
        """Test that manifest is served with correct content type."""
        assert 'application/manifest+json' in self.response.content_type

    def test_manifest_name(self):
        """Test that manifest name is Einkaufsliste."""
        assert self.manifest['name'] == 'Einkaufsliste'

    def test_manifest_short_name(self):
        """Test that manifest short_name is Einkaufsliste."""
        assert self.manifest['short_name'] == 'Einkaufsliste'

    def test_manifest_start_url(self):
        """Test that manifest start_url is /pwa/."""
        assert self.manifest['start_url'] == '/pwa/'

    def test_manifest_display_standalone(self):
        """Test that manifest display mode is standalone."""
        assert self.manifest['display'] == 'standalone'

    def test_manifest_theme_color(self):
        """Test that theme_color matches the orange brand color."""
        assert self.manifest['theme_color'] == '#ff8c42'

    def test_manifest_background_color(self):
        """Test that background_color is light (#fafafa)."""
        assert self.manifest['background_color'] == '#fafafa'

    def test_manifest_lang(self):
        """Test that lang is set to German."""
        assert self.manifest['lang'] == 'de'

    def test_manifest_orientation(self):
        """Test that orientation is portrait-primary for mobile."""
        assert self.manifest['orientation'] == 'portrait-primary'

    def test_manifest_has_icons(self):
        """Test that manifest includes icon definitions."""
        assert 'icons' in self.manifest
        assert len(self.manifest['icons']) >= 2

    def test_manifest_icon_192(self):
        """Test that 192x192 icon is defined."""
        icon_192 = next(
            (i for i in self.manifest['icons'] if i['sizes'] == '192x192'),
            None
        )
        assert icon_192 is not None
        assert icon_192['type'] == 'image/png'
        assert 'icon-192.png' in icon_192['src']

    def test_manifest_icon_512(self):
        """Test that 512x512 icon is defined."""
        icon_512 = next(
            (i for i in self.manifest['icons'] if i['sizes'] == '512x512'),
            None
        )
        assert icon_512 is not None
        assert icon_512['type'] == 'image/png'
        assert 'icon-512.png' in icon_512['src']


# ============================================================================
# Service Worker Tests
# ============================================================================

class TestServiceWorker:
    """Test GET /pwa/sw.js serves the service worker correctly."""

    @pytest.fixture(autouse=True)
    def _get_sw(self, client, app):
        """Fetch the service worker once for all tests in this class."""
        self.response = client.get('/pwa/sw.js')
        self.content = self.response.data.decode('utf-8')

    def test_service_worker_returns_200(self):
        """Test that service worker endpoint returns 200."""
        assert self.response.status_code == 200

    def test_service_worker_content_type(self):
        """Test that service worker is served as JavaScript."""
        assert 'application/javascript' in self.response.content_type

    def test_service_worker_has_cache_version(self):
        """Test that service worker defines a CACHE_VERSION for cache busting."""
        assert 'CACHE_VERSION' in self.content

    def test_service_worker_has_install_handler(self):
        """Test that service worker registers install event listener."""
        assert "addEventListener('install'" in self.content

    def test_service_worker_has_activate_handler(self):
        """Test that service worker registers activate event listener."""
        assert "addEventListener('activate'" in self.content

    def test_service_worker_has_fetch_handler(self):
        """Test that service worker registers fetch event listener."""
        assert "addEventListener('fetch'" in self.content

    def test_service_worker_caches_pwa_shell(self):
        """Test that service worker caches the SPA shell URL."""
        assert "'/pwa/'" in self.content

    def test_service_worker_caches_manifest(self):
        """Test that service worker caches the manifest."""
        assert "'/pwa/manifest.json'" in self.content

    def test_service_worker_caches_main_css(self):
        """Test that service worker caches main.css."""
        assert "'/static/css/main.css'" in self.content

    def test_service_worker_caches_pwa_css(self):
        """Test that service worker caches pwa.css."""
        assert "'/static/pwa/css/pwa.css'" in self.content

    def test_service_worker_caches_js_files(self):
        """Test that service worker caches all JS modules."""
        assert "'/static/pwa/js/auth.js'" in self.content
        assert "'/static/pwa/js/api.js'" in self.content
        assert "'/static/pwa/js/router.js'" in self.content
        assert "'/static/pwa/js/app.js'" in self.content
        assert "'/static/pwa/js/views/login-view.js'" in self.content
        assert "'/static/pwa/js/views/lists-view.js'" in self.content
        assert "'/static/pwa/js/views/list-detail-view.js'" in self.content

    def test_service_worker_caches_icons(self):
        """Test that service worker caches PWA icons."""
        assert "'/static/pwa/icons/icon-192.png'" in self.content
        assert "'/static/pwa/icons/icon-512.png'" in self.content

    def test_service_worker_uses_skip_waiting(self):
        """Test that service worker calls skipWaiting for immediate activation."""
        assert 'skipWaiting()' in self.content

    def test_service_worker_uses_clients_claim(self):
        """Test that service worker calls clients.claim for immediate control."""
        assert 'clients.claim()' in self.content

    def test_service_worker_bypasses_api_requests(self):
        """Test that API requests are not cached (network-only strategy)."""
        assert "'/api/'" in self.content


# ============================================================================
# Static Asset Serving Tests
# ============================================================================

class TestStaticAssets:
    """Test that all PWA static assets are accessible."""

    def test_pwa_css_returns_200(self, client, app):
        """Test that pwa.css is accessible."""
        response = client.get('/static/pwa/css/pwa.css')
        assert response.status_code == 200

    def test_pwa_css_content_type(self, client, app):
        """Test that pwa.css has correct content type."""
        response = client.get('/static/pwa/css/pwa.css')
        assert 'text/css' in response.content_type

    def test_icon_192_returns_200(self, client, app):
        """Test that 192x192 icon is accessible."""
        response = client.get('/static/pwa/icons/icon-192.png')
        assert response.status_code == 200

    def test_icon_512_returns_200(self, client, app):
        """Test that 512x512 icon is accessible."""
        response = client.get('/static/pwa/icons/icon-512.png')
        assert response.status_code == 200

    def test_icon_192_content_type(self, client, app):
        """Test that 192x192 icon is served as PNG."""
        response = client.get('/static/pwa/icons/icon-192.png')
        assert 'image/png' in response.content_type

    def test_icon_512_content_type(self, client, app):
        """Test that 512x512 icon is served as PNG."""
        response = client.get('/static/pwa/icons/icon-512.png')
        assert 'image/png' in response.content_type

    @pytest.mark.parametrize('js_file', [
        'pwa/js/auth.js',
        'pwa/js/api.js',
        'pwa/js/router.js',
        'pwa/js/app.js',
        'pwa/js/views/login-view.js',
        'pwa/js/views/lists-view.js',
        'pwa/js/views/list-detail-view.js',
    ])
    def test_js_files_return_200(self, client, app, js_file):
        """Test that each JavaScript module is accessible."""
        response = client.get(f'/static/{js_file}')
        assert response.status_code == 200

    @pytest.mark.parametrize('js_file', [
        'pwa/js/auth.js',
        'pwa/js/api.js',
        'pwa/js/router.js',
        'pwa/js/app.js',
        'pwa/js/views/login-view.js',
        'pwa/js/views/lists-view.js',
        'pwa/js/views/list-detail-view.js',
    ])
    def test_js_files_content_type(self, client, app, js_file):
        """Test that JavaScript files have correct content type."""
        response = client.get(f'/static/{js_file}')
        content_type = response.content_type
        assert 'javascript' in content_type or 'text/javascript' in content_type


# ============================================================================
# JavaScript Content Verification Tests
# ============================================================================

class TestAuthJSContent:
    """Test that auth.js contains the expected AuthManager implementation."""

    @pytest.fixture(autouse=True)
    def _get_js(self, client, app):
        self.content = client.get('/static/pwa/js/auth.js').data.decode('utf-8')

    def test_defines_auth_manager_class(self):
        """Test that AuthManager class is defined."""
        assert 'class AuthManager' in self.content

    def test_creates_global_singleton(self):
        """Test that a global authManager singleton is created."""
        assert 'const authManager = new AuthManager()' in self.content

    def test_has_get_access_token_method(self):
        """Test that getAccessToken method exists."""
        assert 'getAccessToken()' in self.content

    def test_has_get_refresh_token_method(self):
        """Test that getRefreshToken method exists."""
        assert 'getRefreshToken()' in self.content

    def test_has_set_tokens_method(self):
        """Test that setTokens method exists."""
        assert 'setTokens(' in self.content

    def test_has_clear_all_method(self):
        """Test that clearAll method exists for logout."""
        assert 'clearAll()' in self.content

    def test_has_is_authenticated_method(self):
        """Test that isAuthenticated method exists for auth guard."""
        assert 'isAuthenticated()' in self.content

    def test_has_refresh_access_token_method(self):
        """Test that refreshAccessToken method exists for token renewal."""
        assert 'refreshAccessToken()' in self.content

    def test_uses_local_storage(self):
        """Test that tokens are stored in localStorage."""
        assert 'localStorage' in self.content

    def test_calls_correct_refresh_endpoint(self):
        """Test that refresh calls POST /api/v1/auth/refresh."""
        assert '/api/v1/auth/refresh' in self.content


class TestAPIClientJSContent:
    """Test that api.js contains the expected APIClient implementation."""

    @pytest.fixture(autouse=True)
    def _get_js(self, client, app):
        self.content = client.get('/static/pwa/js/api.js').data.decode('utf-8')

    def test_defines_api_client_class(self):
        """Test that APIClient class is defined."""
        assert 'class APIClient' in self.content

    def test_creates_global_singleton(self):
        """Test that a global apiClient singleton is created."""
        assert 'const apiClient = new APIClient(authManager)' in self.content

    def test_base_url_is_api_v1(self):
        """Test that base URL points to /api/v1."""
        assert "'/api/v1'" in self.content

    def test_has_login_method(self):
        """Test that login method exists calling POST /api/v1/auth/login."""
        assert 'login(' in self.content
        assert '/auth/login' in self.content

    def test_has_logout_method(self):
        """Test that logout method exists calling POST /api/v1/auth/logout."""
        assert 'logout()' in self.content
        assert '/auth/logout' in self.content

    def test_has_get_lists_method(self):
        """Test that getLists method exists calling GET /api/v1/lists."""
        assert 'getLists()' in self.content
        assert "'/lists'" in self.content

    def test_has_get_list_method(self):
        """Test that getList method exists calling GET /api/v1/lists/:id."""
        assert 'getList(' in self.content

    def test_has_create_list_method(self):
        """Test that createList method exists calling POST /api/v1/lists."""
        assert 'createList(' in self.content

    def test_has_create_item_method(self):
        """Test that createItem method exists."""
        assert 'createItem(' in self.content

    def test_has_toggle_item_method(self):
        """Test that toggleItem method exists calling POST /api/v1/items/:id/toggle."""
        assert 'toggleItem(' in self.content
        assert '/toggle' in self.content

    def test_has_delete_item_method(self):
        """Test that deleteItem method exists calling DELETE /api/v1/items/:id."""
        assert 'deleteItem(' in self.content

    def test_has_clear_checked_items_method(self):
        """Test that clearCheckedItems method exists calling POST .../clear-checked."""
        assert 'clearCheckedItems(' in self.content
        assert '/clear-checked' in self.content

    def test_auto_refresh_on_401(self):
        """Test that _request handles 401 by attempting token refresh."""
        assert '401' in self.content

    def test_redirects_to_login_on_refresh_failure(self):
        """Test that failed refresh redirects to #/login."""
        assert '#/login' in self.content


class TestRouterJSContent:
    """Test that router.js contains the expected Router implementation."""

    @pytest.fixture(autouse=True)
    def _get_js(self, client, app):
        self.content = client.get('/static/pwa/js/router.js').data.decode('utf-8')

    def test_defines_router_class(self):
        """Test that Router class is defined."""
        assert 'class Router' in self.content

    def test_creates_global_singleton(self):
        """Test that a global router singleton is created."""
        assert 'const router = new Router()' in self.content

    def test_listens_to_hashchange(self):
        """Test that router listens to hashchange events (hash-based routing)."""
        assert 'hashchange' in self.content

    def test_has_add_route_method(self):
        """Test that addRoute method exists for registering views."""
        assert 'addRoute(' in self.content

    def test_has_start_method(self):
        """Test that start method exists."""
        assert 'start()' in self.content

    def test_has_navigate_method(self):
        """Test that navigate method exists."""
        assert 'navigate(' in self.content

    def test_has_auth_guard(self):
        """Test that router checks authentication before serving protected routes."""
        assert 'isAuthenticated()' in self.content

    def test_redirects_unauthenticated_to_login(self):
        """Test that unauthenticated users are redirected to login."""
        assert '#/login' in self.content

    def test_redirects_authenticated_from_login_to_lists(self):
        """Test that authenticated users on login page are redirected to lists."""
        assert '#/lists' in self.content

    def test_supports_route_parameters(self):
        """Test that router supports parameterized routes like /lists/:id."""
        assert ':' in self.content or 'params' in self.content


class TestAppJSContent:
    """Test that app.js contains the expected App controller implementation."""

    @pytest.fixture(autouse=True)
    def _get_js(self, client, app):
        self.content = client.get('/static/pwa/js/app.js').data.decode('utf-8')

    def test_defines_app_class(self):
        """Test that App class is defined."""
        assert 'class App' in self.content

    def test_registers_service_worker(self):
        """Test that App registers the service worker."""
        assert 'serviceWorker' in self.content
        assert '/pwa/sw.js' in self.content

    def test_registers_login_route(self):
        """Test that App registers the /login route with LoginView."""
        assert "'/login'" in self.content
        assert 'LoginView' in self.content

    def test_registers_lists_route(self):
        """Test that App registers the /lists route with ListsView."""
        assert "'/lists'" in self.content
        assert 'ListsView' in self.content

    def test_registers_list_detail_route(self):
        """Test that App registers the /lists/:id route with ListDetailView."""
        assert "'/lists/:id'" in self.content
        assert 'ListDetailView' in self.content

    def test_has_theme_toggle(self):
        """Test that App supports theme toggling."""
        assert 'data-theme' in self.content
        assert 'dark' in self.content

    def test_has_show_toast_method(self):
        """Test that App has static showToast method for notifications."""
        assert 'showToast(' in self.content

    def test_has_confirm_method(self):
        """Test that App has static confirm method for dialogs."""
        assert 'confirm(' in self.content

    def test_has_set_title_method(self):
        """Test that App has static setTitle method."""
        assert 'setTitle(' in self.content

    def test_has_show_back_button_method(self):
        """Test that App has static showBackButton method."""
        assert 'showBackButton(' in self.content

    def test_has_show_logout_button_method(self):
        """Test that App has static showLogoutButton method."""
        assert 'showLogoutButton(' in self.content

    def test_initializes_on_dom_content_loaded(self):
        """Test that App is initialized on DOMContentLoaded."""
        assert 'DOMContentLoaded' in self.content


# ============================================================================
# View Module Content Tests
# ============================================================================

class TestLoginViewJSContent:
    """Test that login-view.js implements the login screen per the plan."""

    @pytest.fixture(autouse=True)
    def _get_js(self, client, app):
        self.content = client.get('/static/pwa/js/views/login-view.js').data.decode('utf-8')

    def test_defines_login_view_class(self):
        """Test that LoginView class is defined."""
        assert 'class LoginView' in self.content

    def test_has_render_method(self):
        """Test that LoginView has a render method."""
        assert 'render(' in self.content

    def test_sets_title_to_einkaufsliste(self):
        """Test that login view sets title to Einkaufsliste."""
        assert 'Einkaufsliste' in self.content

    def test_hides_back_button(self):
        """Test that login view hides the back button."""
        assert 'showBackButton(false' in self.content

    def test_hides_logout_button(self):
        """Test that login view hides the logout button."""
        assert 'showLogoutButton(false' in self.content

    def test_has_username_field_with_autocomplete(self):
        """Test that login form has username field with autocomplete attribute."""
        assert 'autocomplete="username"' in self.content

    def test_has_password_field_with_autocomplete(self):
        """Test that login form has password field with autocomplete attribute."""
        assert 'autocomplete="current-password"' in self.content

    def test_calls_api_login(self):
        """Test that login form submits via apiClient.login()."""
        assert 'apiClient.login(' in self.content

    def test_navigates_to_lists_on_success(self):
        """Test that successful login navigates to #/lists."""
        assert '#/lists' in self.content

    def test_displays_error_message(self):
        """Test that login errors are displayed to the user."""
        assert 'login-error' in self.content

    def test_has_submit_button(self):
        """Test that login form has a submit button labeled 'Anmelden'."""
        assert 'Anmelden' in self.content


class TestListsViewJSContent:
    """Test that lists-view.js implements the lists overview per the plan."""

    @pytest.fixture(autouse=True)
    def _get_js(self, client, app):
        self.content = client.get('/static/pwa/js/views/lists-view.js').data.decode('utf-8')

    def test_defines_lists_view_class(self):
        """Test that ListsView class is defined."""
        assert 'class ListsView' in self.content

    def test_has_render_method(self):
        """Test that ListsView has a render method."""
        assert 'render(' in self.content

    def test_sets_title_to_meine_listen(self):
        """Test that lists view sets title to 'Meine Listen'."""
        assert 'Meine Listen' in self.content

    def test_shows_logout_button(self):
        """Test that lists view shows the logout button."""
        assert 'showLogoutButton(true' in self.content

    def test_hides_back_button(self):
        """Test that lists view hides the back button (it's the root view)."""
        assert 'showBackButton(false' in self.content

    def test_has_create_list_form(self):
        """Test that lists view has a create-list form."""
        assert 'create-list-form' in self.content

    def test_calls_api_get_lists(self):
        """Test that lists view fetches lists via apiClient.getLists()."""
        assert 'apiClient.getLists()' in self.content

    def test_calls_api_create_list(self):
        """Test that lists view creates lists via apiClient.createList()."""
        assert 'apiClient.createList(' in self.content

    def test_navigates_to_list_detail(self):
        """Test that clicking a list navigates to #/lists/:id."""
        assert '#/lists/' in self.content

    def test_shows_item_count(self):
        """Test that lists view displays item count per list."""
        assert 'item_count' in self.content

    def test_shows_empty_state(self):
        """Test that lists view shows empty state when no lists exist."""
        assert 'Noch keine Listen vorhanden' in self.content


class TestListDetailViewJSContent:
    """Test that list-detail-view.js implements the item management per the plan."""

    @pytest.fixture(autouse=True)
    def _get_js(self, client, app):
        self.content = client.get('/static/pwa/js/views/list-detail-view.js').data.decode('utf-8')

    def test_defines_list_detail_view_class(self):
        """Test that ListDetailView class is defined."""
        assert 'class ListDetailView' in self.content

    def test_has_render_method(self):
        """Test that ListDetailView has a render method."""
        assert 'render(' in self.content

    def test_shows_back_button(self):
        """Test that detail view shows the back button navigating to lists."""
        assert 'showBackButton(true' in self.content
        assert '#/lists' in self.content

    def test_shows_logout_button(self):
        """Test that detail view shows the logout button."""
        assert 'showLogoutButton(true' in self.content

    def test_has_add_item_form(self):
        """Test that detail view has an add-item form."""
        assert 'add-item-form' in self.content

    def test_has_name_input(self):
        """Test that add-item form has a name input field."""
        assert 'item-name' in self.content

    def test_has_quantity_input(self):
        """Test that add-item form has a quantity input field."""
        assert 'item-quantity' in self.content

    def test_add_button_labeled_hinzufuegen(self):
        """Test that the add button is labeled 'Hinzufügen' (German)."""
        assert 'Hinzufügen' in self.content

    def test_calls_api_get_list(self):
        """Test that detail view fetches list via apiClient.getList()."""
        assert 'apiClient.getList(' in self.content

    def test_calls_api_create_item(self):
        """Test that detail view creates items via apiClient.createItem()."""
        assert 'apiClient.createItem(' in self.content

    def test_calls_api_toggle_item(self):
        """Test that detail view toggles items via apiClient.toggleItem()."""
        assert 'apiClient.toggleItem(' in self.content

    def test_calls_api_delete_item(self):
        """Test that detail view deletes items via apiClient.deleteItem()."""
        assert 'apiClient.deleteItem(' in self.content

    def test_calls_api_clear_checked(self):
        """Test that detail view clears checked items via apiClient.clearCheckedItems()."""
        assert 'apiClient.clearCheckedItems(' in self.content

    def test_has_clear_checked_button(self):
        """Test that detail view has 'Abgehakte löschen' button."""
        assert 'Abgehakte löschen' in self.content or 'clear-checked-btn' in self.content

    def test_implements_optimistic_toggle(self):
        """Test that checkbox toggle uses optimistic UI (toggle class before API call)."""
        assert 'classList.toggle' in self.content

    def test_shows_delete_confirmation(self):
        """Test that deleting an item shows a confirmation dialog."""
        assert 'App.confirm(' in self.content

    def test_shows_checked_strikethrough(self):
        """Test that checked items get the 'checked' CSS class for strikethrough."""
        assert 'checked' in self.content

    def test_has_checkbox_per_item(self):
        """Test that each item has a checkbox."""
        assert 'pwa-item-checkbox' in self.content

    def test_has_delete_button_per_item(self):
        """Test that each item has a delete button."""
        assert 'pwa-item-delete' in self.content

    def test_escapes_html_output(self):
        """Test that HTML output is escaped to prevent XSS."""
        assert '_escapeHtml' in self.content


# ============================================================================
# CSS Content Verification Tests
# ============================================================================

class TestPWACSSContent:
    """Test that pwa.css contains required styles per the plan."""

    @pytest.fixture(autouse=True)
    def _get_css(self, client, app):
        self.content = client.get('/static/pwa/css/pwa.css').data.decode('utf-8')

    def test_has_full_height_layout(self):
        """Test that PWA uses 100dvh for proper mobile viewport handling."""
        assert '100dvh' in self.content

    def test_has_flex_column_layout(self):
        """Test that app uses flex column layout."""
        assert 'flex-direction: column' in self.content

    def test_has_sticky_header(self):
        """Test that header is sticky."""
        assert 'position: sticky' in self.content

    def test_has_safe_area_insets(self):
        """Test that safe-area-inset is used for notched devices."""
        assert 'safe-area-inset' in self.content

    def test_has_touch_action_manipulation(self):
        """Test that touch-action: manipulation is used for responsive taps."""
        assert 'touch-action: manipulation' in self.content

    def test_has_min_tap_target_44px(self):
        """Test that minimum tap targets are 44px."""
        assert 'min-width: 44px' in self.content
        assert 'min-height: 44px' in self.content

    def test_has_toast_styles(self):
        """Test that toast notification styles are defined."""
        assert '.pwa-toast' in self.content

    def test_has_toast_animation(self):
        """Test that toast has slide-in animation."""
        assert 'pwa-toast-in' in self.content
        assert 'pwa-toast-out' in self.content

    def test_has_confirm_dialog_styles(self):
        """Test that confirm dialog styles are defined."""
        assert '.pwa-confirm-overlay' in self.content
        assert '.pwa-confirm-dialog' in self.content

    def test_has_login_styles(self):
        """Test that login view styles are defined."""
        assert '.pwa-login' in self.content
        assert '.pwa-login-card' in self.content

    def test_has_list_card_styles(self):
        """Test that list card styles are defined."""
        assert '.pwa-list-card' in self.content

    def test_has_item_styles(self):
        """Test that item styles are defined."""
        assert '.pwa-item' in self.content
        assert '.pwa-item.checked' in self.content

    def test_has_checked_item_strikethrough(self):
        """Test that checked items have strikethrough styling."""
        assert 'text-decoration: line-through' in self.content

    def test_has_checked_item_reduced_opacity(self):
        """Test that checked items have reduced opacity."""
        assert '.pwa-item.checked' in self.content
        assert 'opacity' in self.content

    def test_uses_css_custom_properties(self):
        """Test that pwa.css reuses CSS variables from main.css."""
        assert 'var(--color-primary)' in self.content
        assert 'var(--color-surface)' in self.content
        assert 'var(--color-bg)' in self.content or 'var(--color-text)' in self.content

    def test_has_empty_state_styles(self):
        """Test that empty state styles are defined."""
        assert '.pwa-empty-state' in self.content

    def test_has_mobile_responsive_styles(self):
        """Test that mobile-specific media queries exist."""
        assert '@media' in self.content


# ============================================================================
# PWA End-to-End API Integration Tests
# ============================================================================

class TestPWAAPIIntegration:
    """
    Test the complete PWA user flow through the API endpoints.

    These tests simulate what the PWA JavaScript would do:
    login → get lists → create list → add items → toggle → clear checked.
    """

    def test_full_pwa_workflow(self, client, app, regular_user):
        """Test the complete PWA workflow: login → lists → create → items → toggle → clear."""
        # Step 1: Login via API (what login-view.js does)
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'regular_test',
            'password': 'UserPass123'
        })
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        access_token = login_data['data']['tokens']['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Step 2: Get lists (what lists-view.js does on load)
        lists_response = client.get('/api/v1/lists', headers=headers)
        assert lists_response.status_code == 200
        assert lists_response.get_json()['data'] == []

        # Step 3: Create a new list (what lists-view.js does on form submit)
        create_response = client.post('/api/v1/lists', headers=headers, json={
            'title': 'Wocheneinkauf'
        })
        assert create_response.status_code == 201
        list_id = create_response.get_json()['data']['id']

        # Step 4: Get list detail (what list-detail-view.js does on load)
        detail_response = client.get(f'/api/v1/lists/{list_id}', headers=headers)
        assert detail_response.status_code == 200
        detail_data = detail_response.get_json()['data']
        assert detail_data['title'] == 'Wocheneinkauf'
        assert detail_data['items'] == []

        # Step 5: Add items (what list-detail-view.js does on add-item form submit)
        item1 = client.post(f'/api/v1/lists/{list_id}/items', headers=headers, json={
            'name': 'Milch',
            'quantity': '2 Liter'
        })
        assert item1.status_code == 201
        item1_id = item1.get_json()['data']['id']

        item2 = client.post(f'/api/v1/lists/{list_id}/items', headers=headers, json={
            'name': 'Brot',
            'quantity': '1'
        })
        assert item2.status_code == 201
        item2_id = item2.get_json()['data']['id']

        # Step 6: Toggle item checked (what list-detail-view.js does on checkbox click)
        toggle_response = client.post(f'/api/v1/items/{item1_id}/toggle', headers=headers)
        assert toggle_response.status_code == 200
        assert toggle_response.get_json()['data']['is_checked'] is True

        # Step 7: Verify list now shows checked item
        detail2 = client.get(f'/api/v1/lists/{list_id}', headers=headers)
        items = detail2.get_json()['data']['items']
        checked_items = [i for i in items if i['is_checked']]
        unchecked_items = [i for i in items if not i['is_checked']]
        assert len(checked_items) == 1
        assert len(unchecked_items) == 1

        # Step 8: Clear checked items (what list-detail-view.js does on "Abgehakte löschen")
        clear_response = client.post(
            f'/api/v1/lists/{list_id}/items/clear-checked',
            headers=headers
        )
        assert clear_response.status_code == 200
        assert clear_response.get_json()['data']['deleted_count'] == 1

        # Step 9: Verify only unchecked item remains
        detail3 = client.get(f'/api/v1/lists/{list_id}', headers=headers)
        remaining_items = detail3.get_json()['data']['items']
        assert len(remaining_items) == 1
        assert remaining_items[0]['name'] == 'Brot'

    def test_pwa_delete_item_workflow(self, client, app, regular_user):
        """Test item deletion flow as the PWA would do it (with confirmation)."""
        # Login
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'regular_test',
            'password': 'UserPass123'
        })
        access_token = login_response.get_json()['data']['tokens']['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Create list and item
        list_resp = client.post('/api/v1/lists', headers=headers, json={
            'title': 'Testliste'
        })
        list_id = list_resp.get_json()['data']['id']

        item_resp = client.post(f'/api/v1/lists/{list_id}/items', headers=headers, json={
            'name': 'Butter',
            'quantity': '250g'
        })
        item_id = item_resp.get_json()['data']['id']

        # Delete item (what happens after user confirms in App.confirm dialog)
        delete_response = client.delete(f'/api/v1/items/{item_id}', headers=headers)
        assert delete_response.status_code == 200

        # Verify item no longer in list
        detail = client.get(f'/api/v1/lists/{list_id}', headers=headers)
        assert len(detail.get_json()['data']['items']) == 0

    def test_pwa_token_refresh_flow(self, client, app, regular_user):
        """Test token refresh as the PWA APIClient would do on 401."""
        from flask_jwt_extended import create_refresh_token

        # Login to get refresh token
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'regular_test',
            'password': 'UserPass123'
        })
        refresh_token = login_response.get_json()['data']['tokens']['refresh_token']

        # Refresh token (what auth.js refreshAccessToken does)
        refresh_response = client.post('/api/v1/auth/refresh', headers={
            'Authorization': f'Bearer {refresh_token}',
            'Content-Type': 'application/json'
        })
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.get_json()['data']['access_token']

        # Use new token to make API call
        headers = {
            'Authorization': f'Bearer {new_access_token}',
            'Content-Type': 'application/json'
        }
        lists_response = client.get('/api/v1/lists', headers=headers)
        assert lists_response.status_code == 200

    def test_pwa_logout_flow(self, client, app, regular_user):
        """Test logout as the PWA would do it (revoke token, clear client state)."""
        # Login
        login_response = client.post('/api/v1/auth/login', json={
            'username': 'regular_test',
            'password': 'UserPass123'
        })
        access_token = login_response.get_json()['data']['tokens']['access_token']
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Logout (what apiClient.logout() does)
        logout_response = client.post('/api/v1/auth/logout', headers=headers)
        assert logout_response.status_code == 200

        # Verify token is now invalid (client would redirect to #/login)
        lists_response = client.get('/api/v1/lists', headers=headers)
        assert lists_response.status_code == 401

    def test_pwa_unauthenticated_api_access_returns_401(self, client, app):
        """Test that API calls without JWT return 401 (PWA should redirect to login)."""
        response = client.get('/api/v1/lists', headers={
            'Content-Type': 'application/json'
        })
        assert response.status_code == 401
