// Offline support. The app shell is cached on install; catalogue data is network-first so new NCERT
// material appears as soon as the device is online, with the last copy used when offline.
// Files from ncert.nic.in and YouTube are never touched here – they always open from their own sites.
const BUILD = "__BUILD__";                 // replaced by build_site.py with a hash of the app files
const SHELL = `shell-${BUILD}`;
const DATA = "data-v1";
const SHELL_FILES = ["./", "index.html", "styles.css", "app.js", "i18n.js", "store.js", "ui.js", "search.js",
  "manifest.webmanifest", "icons/icon.svg", "icons/icon-192.png", "icons/icon-512.png"];
const DATA_FILES = ["meta", "learn", "teach", "office", "textbooks", "videos", "changes"].map((n) => `data/${n}.json`);

self.addEventListener("install", (e) => {
  e.waitUntil((async () => {
    await (await caches.open(SHELL)).addAll(SHELL_FILES);
    const data = await caches.open(DATA);
    await Promise.all(DATA_FILES.map((f) => data.add(f).catch(() => {})));   // best effort: whole catalogue offline
    self.skipWaiting();
  })());
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) if (k.startsWith("shell-") && k !== SHELL) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.includes("/data/")) {
    e.respondWith((async () => {
      const cache = await caches.open(DATA);
      try {
        const fresh = await fetch(e.request);
        if (fresh.ok) cache.put(url.pathname.slice(url.pathname.indexOf("data/")), fresh.clone());
        return fresh;
      } catch (err) {
        return (await cache.match(url.pathname.slice(url.pathname.indexOf("data/")))) || Response.error();
      }
    })());
    return;
  }
  e.respondWith((async () => {
    const hit = await caches.match(e.request, { ignoreSearch: true });
    if (hit) return hit;
    try {
      return await fetch(e.request);
    } catch (err) {
      return e.request.mode === "navigate" ? caches.match("index.html") : Response.error();
    }
  })());
});
