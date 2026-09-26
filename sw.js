// أول خطوة: يخلي الموقع يفتح كتطبيق، ويشتغل حتى لو النت ضعيف
const CACHE = "awal-khatwa-v1";
const SHELL = ["./", "index.html", "cv.html", "guide.html", "stats.html", "feedback.js", "manifest.webmanifest", "icon-192.png", "og-image.jpg"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).catch(() => {}));
  self.skipWaiting();
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))));
  self.clients.claim();
});
// نجيب النسخة الجديدة من النت أول، ولو ما فيه نت نرجع للنسخة المحفوظة
self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    fetch(req).then(res => {
      if (res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
      return res;
    }).catch(() => caches.match(req).then(r => r || caches.match("index.html")))
  );
});
