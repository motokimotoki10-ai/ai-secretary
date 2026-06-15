const CACHE_NAME = "ai-secretary-v60-fortune-ocr-20260615";
const STATIC_ASSETS = [
  "/",
  "/static/style.css",
  "/static/license.js",
  "/static/voice.js",
  "/static/pwa.js",
  "/static/display_settings.js",
  "/static/camera.js",
  "/static/business_card_ocr.js",
  "/static/recording.js",
  "/static/summary.js",
  "/static/consult.js",
  "/static/calculator.js",
  "/static/weather.js",
  "/static/travel.js",
  "/static/google_calendar.js",
  "/static/fortune.js",
  "/static/writer.js",
  "/static/logo.png",
  "/static/app_logo.png",
  "/static/apple-touch-icon.png",
  "/static/icon-192.png",
  "/static/icon-512.png",
  "/static/manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      )
    )
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cached) => {
      return cached || fetch(event.request);
    })
  );
});
