const CACHE_NAME = 'resqai-v1.0';
const OFFLINE_URL = '/offline-guide';

const PRECACHE_ASSETS = [
  '/',
  '/offline-guide',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/indexeddb.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js'
];

// Install: Cache offline survival guide and core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS).catch((err) => {
        console.warn('Some pre-cache assets could not be cached immediately:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch Strategy: Network-first with offline fallback for navigation
self.addEventListener('fetch', (event) => {
  const req = event.request;

  // Only handle GET requests
  if (req.method !== 'GET') {
    return;
  }

  // Handle HTML navigation
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).catch(() => {
        return caches.match(OFFLINE_URL).then((cached) => {
          return cached || new Response("You are currently offline. Please reconnect to submit reports.", {
            headers: { 'Content-Type': 'text/plain' }
          });
        });
      })
    );
    return;
  }

  // Handle static assets with Cache-First strategy
  if (req.url.includes('/static/') || req.url.includes('cdn.jsdelivr.net')) {
    event.respondWith(
      caches.match(req).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(req).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(req, responseToCache);
            });
          }
          return networkResponse;
        }).catch(() => caches.match(req));
      })
    );
    return;
  }

  // Standard fetch for everything else
  event.respondWith(
    fetch(req).catch(() => caches.match(req))
  );
});
