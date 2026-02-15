/**
 * Service Worker — App shell caching strategy.
 *
 * - Cache-first for static assets (HTML, CSS, JS, icons, manifest)
 * - Network-only for API requests
 */

const CACHE_VERSION = 'pwa-v1';
const APP_SHELL_URLS = [
  '/pwa/',
  '/pwa/manifest.json',
  '/static/css/main.css',
  '/static/pwa/css/pwa.css',
  '/static/pwa/js/auth.js',
  '/static/pwa/js/api.js',
  '/static/pwa/js/router.js',
  '/static/pwa/js/views/login-view.js',
  '/static/pwa/js/views/lists-view.js',
  '/static/pwa/js/views/list-detail-view.js',
  '/static/pwa/js/app.js',
  '/static/pwa/icons/icon-192.png',
  '/static/pwa/icons/icon-512.png'
];

// Install: cache the app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_VERSION).then((cache) => cache.addAll(APP_SHELL_URLS))
  );
  self.skipWaiting();
});

// Activate: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.filter((key) => key !== CACHE_VERSION).map((key) => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// Fetch: cache-first for app shell, network-only for API
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Network-only for API requests
  if (url.pathname.startsWith('/api/')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) {
        return cached;
      }
      return fetch(event.request);
    })
  );
});
