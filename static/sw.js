// Service Worker for Antidote Medical Marketplace PWA
const CACHE_NAME = 'antidote-v1';
const STATIC_CACHE = 'antidote-static-v1';
const DYNAMIC_CACHE = 'antidote-dynamic-v1';

// Essential files to cache for offline functionality
const ESSENTIAL_FILES = [
  '/',
  '/static/images/antidote-logo-new.png',
  '/static/favicon-32x32.png',
  '/static/manifest.json'
];

// Install event - cache essential files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('[SW] Pre-caching essential files');
        return cache.addAll(ESSENTIAL_FILES);
      })
      .catch(err => {
        console.log('[SW] Pre-cache failed:', err);
      })
  );
  self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', event => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;
  
  // Skip external requests
  if (!event.request.url.startsWith(self.location.origin)) return;

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Return cached version if available
        if (response) {
          console.log('[SW] Serving from cache:', event.request.url);
          return response;
        }

        // Otherwise fetch from network
        return fetch(event.request)
          .then(fetchResponse => {
            // Don't cache non-successful responses
            if (!fetchResponse || fetchResponse.status !== 200 || fetchResponse.type !== 'basic') {
              return fetchResponse;
            }

            // Clone response for caching
            const responseToCache = fetchResponse.clone();
            
            // Cache static assets
            if (event.request.url.includes('/static/')) {
              caches.open(STATIC_CACHE)
                .then(cache => {
                  cache.put(event.request, responseToCache);
                });
            } else {
              // Cache dynamic content with size limit
              caches.open(DYNAMIC_CACHE)
                .then(cache => {
                  cache.put(event.request, responseToCache);
                  // Limit dynamic cache size
                  cache.keys().then(keys => {
                    if (keys.length > 50) {
                      cache.delete(keys[0]);
                    }
                  });
                });
            }

            return fetchResponse;
          })
          .catch(() => {
            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
          });
      })
  );
});

// Background sync for form submissions when offline
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    event.waitUntil(doBackgroundSync());
  }
});

// Push notification handling
self.addEventListener('push', event => {
  if (!event.data) return;

  const data = event.data.json();
  const options = {
    body: data.body,
    icon: '/static/favicon-32x32.png',
    badge: '/static/favicon-16x16.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: data.primaryKey || 1
    },
    actions: [
      {
        action: 'explore',
        title: 'View Details',
        icon: '/static/favicon-16x16.png'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/static/favicon-16x16.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'Antidote', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  event.notification.close();

  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

function doBackgroundSync() {
  // Handle background sync for offline form submissions
  return Promise.resolve();
}