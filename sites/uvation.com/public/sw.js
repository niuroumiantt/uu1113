const CACHE_NAME = "pwa-cache-v1";
const urlsToCache = ["/", "/offline.html"];

// Install
self.addEventListener("install", (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(urlsToCache))
    );
    self.skipWaiting(); // activate immediately
});

// Activate
self.addEventListener("activate", (event) => {
    event.waitUntil(
        caches.keys().then((keys) =>
            Promise.all(keys.map((key) => key !== CACHE_NAME && caches.delete(key)))
        )
    );
    self.clients.claim(); // take control right away
});

// Fetch (network first, cache fallback)
self.addEventListener("fetch", (event) => {
    if (event.request.method !== "GET") return; // skip POST/PUT etc.

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // clone response for caching
                const respClone = response.clone();
                caches.open(CACHE_NAME).then((cache) => cache.put(event.request, respClone));
                return response; // fresh network response
            })
            .catch(() =>
                caches.match(event.request).then((resp) => {
                    if (resp) return resp;
                    return caches.match("/offline.html"); // fallback page
                })
            )
    );
});
