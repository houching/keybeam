const CACHE_NAME = 'keybeam-cache-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/favicon.png',
  '/icons.svg',
  '/manifest.json'
];

// Install: Cache core static shells
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: Clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch: Stale-While-Revalidate pattern (Fast load, background updates)
self.addEventListener('fetch', (event) => {
  // Ignore WebSocket and non-GET requests
  if (event.request.method !== 'GET' || event.request.url.startsWith('ws') || event.request.url.includes('/ws')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const fetchPromise = fetch(event.request).then((networkResponse) => {
        // Cache the newly fetched asset
        if (networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      }).catch(() => {
        // Offline fallback
      });

      // Return cached asset immediately, fallback to network
      return cachedResponse || fetchPromise;
    })
  );
});
