// Small rendering helpers: escaping, cards, chips, video player, toast.
import { t, pick, lang, KINDS, PRODUCTS, LANG_NAMES } from "./i18n.js";
import { isSaved } from "./store.js";

export const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

export function size(bytes) {
  if (!bytes) return "";
  return bytes > 1048576 ? (bytes / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(bytes / 1024)) + " KB";
}
export function date(iso) {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00");
  return d.toLocaleDateString(lang() === "en" ? "en-IN" : "hi-IN", { day: "numeric", month: "short", year: "numeric" });
}

// Main + alternate title in the reader's language order
export function titlePair(it) {
  const hasHi = (s) => /[ऀ-ॿ]/.test(s || "");
  let main = it.t || it.th || "", alt = it.th && it.th !== it.t ? it.th : "";
  if (lang() === "hi" && alt && hasHi(alt) && !hasHi(main)) [main, alt] = [alt, main];
  return [main, alt];
}

export function card(it, opts = {}) {
  const [main, alt] = titlePair(it);
  const k = KINDS[it.k] || KINDS.page;
  const p = it.p && PRODUCTS[it.p];
  const from = it.from ? (lang() === "hi" ? it.from[1] || it.from[0] : it.from[0] || it.from[1]) : "";
  const versions = (it.v || [])
    .map((v) => `<a class="chip ver" href="${esc(v.u)}" target="_blank" rel="noopener noreferrer" data-open="${esc(it.i)}">${esc(pick(...(LANG_NAMES[v.l] || [v.l, v.l])))}${v.z ? " · " + size(v.z) : ""}</a>`)
    .join("");
  const meta = [
    `<span title="${esc(pick(k[1], k[2]))}">${k[0]} ${esc(pick(k[1], k[2]))}</span>`,
    it.z && !it.v ? `<span>${size(it.z)}</span>` : "",
    it.d ? `<span>${esc(t("updated"))} ${date(it.d)}</span>` : "",
    (it.c || []).length ? `<span>${esc(t("classN"))} ${esc(classRange(it.c))}</span>` : "",
    !it.v && (it.l || []).length ? `<span>${esc(it.l.map((l) => pick(...(LANG_NAMES[l] || [l, l]))).join(", "))}</span>` : "",
    p && it.p !== "M" && opts.showProduct ? `<span>${p[0]} ${esc(pick(p[1], p[2]))}</span>` : "",
  ].filter(Boolean).join("");
  const saved = isSaved(it.i);
  return `<article class="card" data-id="${esc(it.i)}">
    <div class="card-main">
      <a class="title" href="${esc(it.u)}" target="_blank" rel="noopener noreferrer" data-open="${esc(it.i)}">${esc(main)}</a>
      ${alt ? `<div class="alt">${esc(alt)}</div>` : ""}
      ${from && from !== main ? `<div class="from">${esc(t("from"))}: ${esc(from)}</div>` : ""}
      ${it.n && !opts.hideNote ? `<p class="note">${esc(it.n)}</p>` : ""}
      <div class="meta">${meta}</div>
      ${versions ? `<div class="versions">${versions}</div>` : ""}
    </div>
    <button class="star${saved ? " on" : ""}" data-act="save" data-id="${esc(it.i)}" aria-pressed="${saved}"
      aria-label="${esc(saved ? t("saved") : t("save"))}" title="${esc(saved ? t("saved") : t("save"))}">${saved ? "★" : "☆"}</button>
  </article>`;
}

function classRange(c) {
  const a = c[0], b = c[c.length - 1];
  return a === b ? String(a) : `${a}–${b}`;
}

export function tiles(list, hrefOf, countOf) {
  return `<div class="tiles">${list
    .map((g) => `<a class="tile" href="${hrefOf(g)}"><span class="ico" aria-hidden="true">${g[1]}</span>
      <span class="tl">${esc(pick(g[2], g[3]))}</span>${g[4] ? `<span class="td">${esc(pick(g[4], g[5]))}</span>` : ""}
      ${countOf ? `<span class="cnt">${countOf(g)}</span>` : ""}</a>`)
    .join("")}</div>`;
}

// ---- toast ----
let toastTimer;
export function toast(msg) {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), 3500);
}

// ---- YouTube player: nothing loads from YouTube until the user presses play ----
const YT = "https://www.youtube-nocookie.com/embed/";
export function playVideos(ids, title) {
  const [first, ...rest] = ids.slice(0, 50);
  openPlayer(`${YT}${encodeURIComponent(first)}?rel=0${rest.length ? "&playlist=" + rest.map(encodeURIComponent).join(",") : ""}`, title);
}
export function playList(listId, title) {
  openPlayer(`${YT}videoseries?list=${encodeURIComponent(listId)}&rel=0`, title);
}
function openPlayer(src, title) {
  closePlayer();
  const box = document.createElement("div");
  box.className = "player";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-label", title || t("videos"));
  box.innerHTML = `<div class="player-in">
      <div class="player-bar"><strong>${esc(title || "")}</strong>
        <button class="btn" data-act="close-player" aria-label="${esc(t("close"))}">✕ ${esc(t("close"))}</button></div>
      <div class="frame"><iframe src="${esc(src)}" title="${esc(title || "YouTube")}" allow="encrypted-media; picture-in-picture; fullscreen"
        allowfullscreen referrerpolicy="strict-origin-when-cross-origin"></iframe></div></div>`;
  document.body.appendChild(box);
  box.querySelector("button").focus();
}
export function closePlayer() {
  document.querySelectorAll(".player").forEach((p) => p.remove());
}
