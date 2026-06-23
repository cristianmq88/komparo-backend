// Service worker mínimo para Komparo (PWA instalable + carga offline básica).
// Estrategia:
//  - Navegaciones: network-first con fallback al index cacheado (app shell).
//  - Estáticos del mismo origen: stale-while-revalidate.
//  - Nunca cachea llamadas a la API (auth, datos en vivo).
const CACHE = "komparo-v1";
const APP_SHELL = ["/", "/index.html", "/manifest.webmanifest", "/komparo.svg"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

function isApi(url) {
  return (
    url.pathname.startsWith("/api") ||
    url.pathname.startsWith("/auth") ||
    url.pathname.startsWith("/lists") ||
    url.pathname.startsWith("/products") ||
    url.pathname.startsWith("/recipes") ||
    url.pathname.startsWith("/supermarkets") ||
    url.pathname.startsWith("/admin")
  );
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isApi(url)) return;

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() => caches.match("/index.html"))
    );
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(request, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
