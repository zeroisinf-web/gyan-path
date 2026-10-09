// Everything the app remembers lives on this device only (localStorage + IndexedDB). Nothing is sent anywhere.

function read(key, fallback) {
  try {
    const v = localStorage.getItem(key);
    return v ? JSON.parse(v) : fallback;
  } catch (e) {
    return fallback;
  }
}
function write(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch (e) { /* private mode / storage full: the app still works, it just forgets */ }
}

export const settings = read("gp.settings", { lang: "hi", theme: "auto" });
export const saveSettings = () => write("gp.settings", settings);

// ---- saved items & recently opened (small snapshots so they show even before data loads) ----
let shelf = read("gp.shelf", []);
let recent = read("gp.recent", []);
const snap = (it) => ({ i: it.i, t: it.t, th: it.th, u: it.u, k: it.k, sec: it.sec, g: it.g });

export const shelfItems = () => shelf;
export const isSaved = (id) => shelf.some((x) => x.i === id);
export function toggleSave(it) {
  shelf = isSaved(it.i) ? shelf.filter((x) => x.i !== it.i) : [snap(it), ...shelf];
  write("gp.shelf", shelf);
  return isSaved(it.i);
}
export const recentItems = () => recent;
export function addRecent(it) {
  recent = [snap(it), ...recent.filter((x) => x.i !== it.i)].slice(0, 12);
  write("gp.recent", recent);
}

export const lastSeenChanges = () => read("gp.seen", "");
export const markChangesSeen = (date) => write("gp.seen", date);
export const knownVersion = () => read("gp.version", "");
export const setKnownVersion = (v) => write("gp.version", v);

// ---- data (data/*.json, cached for offline by the service worker) ----
const cache = {};
export async function load(name) {
  if (!cache[name]) {
    cache[name] = fetch(`data/${name}.json`, { cache: "no-cache" })
      .then((r) => {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then((j) => expand(name, j))
      .catch((e) => {
        delete cache[name];
        throw e;
      });
  }
  return cache[name];
}
export function forgetData() {
  for (const k of Object.keys(cache)) delete cache[k];
}

// Section files store repeated strings once; give every item its full text back.
function expand(name, j) {
  if (!["learn", "teach", "office"].includes(name)) return j;
  for (const it of j.items) {
    it.sec = name;
    if (typeof it.n === "number") it.n = j.notes[it.n];
    if (typeof it.s === "number") it.s = j.sections[it.s];
    if (it.pp && j.pages[it.pp]) it.from = j.pages[it.pp];
  }
  return j;
}

// ---- my offline PDFs (IndexedDB) ----
const DB = "gp-offline", STORE = "files";
function db() {
  return new Promise((res, rej) => {
    const r = indexedDB.open(DB, 1);
    r.onupgradeneeded = () => r.result.createObjectStore(STORE, { keyPath: "id", autoIncrement: true });
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}
async function tx(mode, fn) {
  const d = await db();
  return new Promise((res, rej) => {
    const t = d.transaction(STORE, mode);
    const out = fn(t.objectStore(STORE));
    t.oncomplete = () => res(out && out.result !== undefined ? out.result : out);
    t.onerror = () => rej(t.error);
  });
}
export const addOfflineFile = (file) =>
  tx("readwrite", (s) => s.add({ name: file.name, size: file.size, added: Date.now(), blob: file }));
export const listOfflineFiles = () => tx("readonly", (s) => s.getAll());
export const deleteOfflineFile = (id) => tx("readwrite", (s) => s.delete(id));
export const getOfflineFile = (id) => tx("readonly", (s) => s.get(id));
