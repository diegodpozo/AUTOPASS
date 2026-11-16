/* AUTOPASS PWA - Service Worker
   - Precaché del app shell para carga offline/instantánea.
   - Páginas (navegación): network-first con fallback offline.html.
   - Estáticos y CDN: stale-while-revalidate.
   - API (/v1) y mutaciones: SOLO red (nunca se cachean).
   - Al desplegar una versión nueva, subir CACHE_NAME (ej. autopass-v2). */
const CACHE_NAME = "autopass-v25";
const SHELL_CACHE = "autopass-shell-v24";
const RUNTIME_CACHE = "autopass-runtime-v1";
const PRECACHE = [
  "/manifest.webmanifest",
  "/static/offline.html",
  "/static/css/base/variables.css",
  "/static/css/base/reset.css",
  "/static/css/base/typography.css",
  "/static/css/base/utilities.css",
  "/static/css/base/animations.css",
  "/static/css/components/buttons.css",
  "/static/css/components/cards.css",
  "/static/css/components/forms.css",
  "/static/css/components/tables.css",
  "/static/css/components/badges.css",
  "/static/css/components/modals.css",
  "/static/css/components/action-menu.css",
  "/static/css/components/footer.css",
  "/static/css/components/virtual-time.css",
  "/static/css/layout/grid.css",
  "/static/css/layout/sidebar.css",
  "/static/css/layout/header.css",
  "/static/css/layout/standalone.css",
  "/static/css/style.css",
  "/static/css/pages/landing/landing-features.css",
  "/static/css/pages/landing/landing-hero.css",
  "/static/css/pages/landing/landing-map.css",
  "/static/css/pages/landing/landing-modals.css",
  "/static/css/pages/landing/landing-nav.css",
  "/static/css/pages/dashboard/dashboard-base.css",
  "/static/css/pages/dashboard/dashboard-cards.css",
  "/static/css/pages/dashboard/dashboard-tables.css",
  "/static/css/pages/dashboard/dashboard-settings.css",
  "/static/css/pages/dashboard/dashboard-live.css",
  "/static/css/pages/dashboard/dashboard-admin-tour.css",
  "/static/css/pages/profile/profile-base.css",
  "/static/css/pages/legal.css",
  "/static/js/api_client.js",
  "/static/js/main.js",
  "/static/js/landing.js",
  "/static/js/dashboard.js",
  "/static/js/perfil.js",
  "/static/js/reservas.js",
  "/static/js/auth.js",
  "/static/js/modules/api.js",
  "/static/js/modules/ui.js",
  "/static/js/modules/utils.js",
  "/static/js/modules/landing.js",
  "/static/js/modules/landing-data.js",
  "/static/js/modules/landing-map.js",
  "/static/js/modules/landing-map-state.js",
  "/static/js/modules/landing-map-data.js",
  "/static/js/modules/landing-map-pois.js",
  "/static/js/modules/landing-map-geo.js",
  "/static/js/modules/landing-map-locality.js",
  "/static/js/modules/landing-carousel.js",
  "/static/js/modules/dashboard-ui.js",
  "/static/js/modules/drag-sort.js",
  "/static/js/modules/action-menu.js",
  "/static/js/modules/dashboard-admin.js",
  "/static/js/modules/dashboard-stats.js",
  "/static/js/modules/operator-alerts.js",
  "/static/js/modules/dashboard-operations.js",
  "/static/js/modules/dashboard-reservations.js",
  "/static/js/modules/reservations-admin-list.js",
  "/static/js/modules/reservations-admin-form.js",
  "/static/js/modules/dashboard-finance.js",
  "/static/js/modules/dashboard-metrics.js",
  "/static/js/modules/dashboard-informes.js",
  "/static/js/modules/report-html-export.js",
  "/static/js/modules/profile.js",
  "/static/js/modules/reservas.js",
  "/static/js/modules/reservas-form.js",
  "/static/js/modules/reservas-form-state.js",
  "/static/js/modules/reservas-form-price.js",
  "/static/js/modules/reservas-form-slot.js",
  "/static/js/modules/reservas-actions.js",
  "/static/js/modules/reservas-list.js",
  "/static/js/modules/reservas-pass.js",
  "/static/js/modules/vehicles.js",
  "/static/js/modules/notifications.js",
  "/static/js/modules/notifications-state.js",
  "/static/js/modules/notifications-format.js",
  "/static/js/modules/notifications-render.js",
  "/static/js/modules/notifications-badge.js",
  "/static/js/modules/notifications-actions.js",
  "/static/js/modules/notifications-nav.js",
  "/static/js/modules/notifications-dropdown.js",
  "/static/js/modules/notifications-polling.js",
  "/static/js/modules/tour.js",
  "/static/js/modules/tour-steps.js",
  "/static/js/modules/admin-tour.js",
  "/static/js/modules/admin-tour-steps.js",
  "/static/js/modules/admin-tour-engine.js",
  "/static/js/modules/admin-help.js",
  "/static/js/modules/virtual-time.js",
  "/static/images/logo.png",
  "/static/images/background.jpg",
  "/static/images/icons/icon-192.png",
  "/static/images/icons/icon-512.png"
];
const CDN_HOSTS = ["unpkg.com", "cdnjs.cloudflare.com", "cdn.jsdelivr.net", "npmcdn.com"];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(SHELL_CACHE)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => ![SHELL_CACHE, RUNTIME_CACHE].includes(k)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

const isNavigation = req => req.mode === "navigate";
const isAPI = req => new URL(req.url).pathname.startsWith("/v1/");
const isAuth = req => new URL(req.url).pathname.includes("/auth/");
const isStatic = req => {
  const u = new URL(req.url);
  return u.origin === self.location.origin && /\.(css|js|png|jpg|jpeg|webp|svg|ico|woff2?|ttf|otf|gif)$/.test(u.pathname);
};
const isCDN = req => {
  try {
    const host = new URL(req.url).hostname;
    return CDN_HOSTS.includes(host);
  } catch (e) { return false; }
};

function putInCache(cacheName, request, response) {
  if (!response || response.status !== 200) return Promise.resolve();
  const copy = response.clone();
  return caches.open(cacheName).then(cache => cache.put(request, copy)).catch(() => {});
}

async function staleWhileRevalidate(request, cacheName) {
  const cached = await caches.match(request);
  const network = fetch(request)
    .then(resp => {
      if (resp) {
        putInCache(cacheName, request, resp.clone());
        return resp;
      }
      return null;
    })
    .catch(() => null);

  if (cached) return cached;
  const fresh = await network;
  return fresh || Response.error();
}

async function networkFirst(request) {
  try {
    const resp = await fetch(request);
    if (resp.status === 200) {
      const copy = resp.clone();
      const cache = await caches.open(RUNTIME_CACHE);
      cache.put(request, copy).catch(() => {});
    }
    return resp;
  } catch (e) {
    const cached = await caches.match(request);
    if (cached) return cached;
    const offline = await caches.match("/static/offline.html");
    if (offline) return offline;
    return new Response("Sin conexión", { status: 503, headers: { "Content-Type": "text/plain" } });
  }
}

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return; // POST/PUT/DELETE siempre van a red

  if (isNavigation(req)) {
    event.respondWith(networkFirst(req));
    return;
  }
  if (isAuth(req)) return; // endpoints de login: nunca cachear
  if (isAPI(req)) return;  // API de negocio: solo red

  if (isStatic(req)) {
    event.respondWith(networkFirst(req));
    return;
  }
  if (isCDN(req)) {
    event.respondWith(staleWhileRevalidate(req, RUNTIME_CACHE));
  }
});