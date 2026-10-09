// Router + views. Hash routes (#/learn/practice) so the app works from any static host and offline.
import { t, pick, lang, setLang, GROUPS, PRODUCTS, KINDS, LANG_NAMES, groupInfo } from "./i18n.js";
import * as store from "./store.js";
import { esc, card, tiles, toast, playVideos, playList, closePlayer, date, size, titlePair } from "./ui.js";
import { search, resetSearch } from "./search.js";

const main = document.getElementById("main");
const REG = new Map();          // item id -> item, for the ★ save button and "recently opened"
const PAGE = 40;
const CLASS_LABEL = (c) => (c === 13 ? "XI–XII" : c === 14 ? pick("व्यावसायिक", "Vocational") : String(c));

// ---------------------------------------------------------------- shell
function applyTheme() {
  const th = store.settings.theme;
  if (th === "light" || th === "dark") document.documentElement.dataset.theme = th;
  else delete document.documentElement.dataset.theme;
}

function renderChrome() {
  document.documentElement.lang = lang();
  document.title = `${t("app")} – ${t("tagline")}`;
  document.getElementById("brand").innerHTML = `<span class="logo" aria-hidden="true">ज्ञ</span><span>${esc(t("app"))}</span>`;
  document.getElementById("langBtn").textContent = lang() === "hi" ? "EN" : "हि";
  document.getElementById("langBtn").setAttribute("aria-label", lang() === "hi" ? "Switch to English" : "हिंदी में देखें");
  document.getElementById("searchBtn").setAttribute("aria-label", t("search"));
  document.getElementById("newBtn").setAttribute("aria-label", t("whatsnew"));
  document.getElementById("aboutBtn").setAttribute("aria-label", t("about"));
  const tabs = [["", "🏠", t("home")], ["learn", "📚", t("learn")], ["teach", "🧑‍🏫", t("teach")], ["office", "🏛️", t("office")], ["shelf", "★", t("shelf")]];
  const cur = route().parts[0] || "";
  const curTab = ["books", "book", "class", "videos"].includes(cur) ? "learn" : cur;
  document.getElementById("tabs").innerHTML = tabs
    .map(([r, ico, label]) => `<a href="#/${r}" class="${curTab === r ? "on" : ""}" ${curTab === r ? 'aria-current="page"' : ""}>
      <span aria-hidden="true">${ico}</span><span>${esc(label)}</span></a>`).join("");
  document.getElementById("foot").innerHTML = `${esc(t("copyright"))} · <a href="#/about">${esc(t("about"))}</a>`;
  document.getElementById("offline").textContent = t("offlineNow");
}

function route() {
  const [path, query] = location.hash.replace(/^#\/?/, "").split("?");
  return { parts: path.split("/").filter(Boolean).map(decodeURIComponent), q: new URLSearchParams(query || "") };
}

async function render() {
  closePlayer();
  renderChrome();
  const { parts, q } = route();
  const [a, b] = parts;
  main.innerHTML = `<div class="loading">…</div>`;
  try {
    if (!a) await vHome();
    else if (a === "learn" && !b) await vSection("learn");
    else if (a === "learn" && b === "books") location.hash = "#/books";
    else if (a === "learn" && b === "media") location.hash = "#/videos";
    else if (a === "books" && !b) await vBooks();
    else if (a === "books") await vBooksClass(+b);
    else if (a === "book") await vBook(b, q.get("v"));
    else if (a === "class") await vClass(+b);
    else if (a === "videos") await vVideos("learn");
    else if (["learn", "teach", "office"].includes(a) && b) await vList(a, b, Object.fromEntries(q));
    else if (a === "teach" || a === "office") await vSection(a);
    else if (a === "new") await vNew(q.get("tab") || "learn");
    else if (a === "shelf") await vShelf();
    else if (a === "search") await vSearch(q.get("q") || "");
    else if (a === "about") await vAbout();
    else main.innerHTML = `<p class="empty">${esc(t("none"))}</p>`;
  } catch (e) {
    console.error(e);
    main.innerHTML = `<p class="empty">${esc(pick("डेटा लोड नहीं हो सका। इंटरनेट जाँचें और फिर कोशिश करें।",
      "Could not load the data. Check your connection and try again."))}</p>`;
  }
  main.focus({ preventScroll: true });
  window.scrollTo(0, 0);
}

const reg = (items) => { for (const it of items) REG.set(it.i, it); return items; };
const head = (title, sub, back) =>
  `<div class="head">${back ? `<a class="back" href="${back}" aria-label="${esc(pick("पीछे", "Back"))}">‹</a>` : ""}<div>
    <h1>${esc(title)}</h1>${sub ? `<p class="sub">${esc(sub)}</p>` : ""}</div></div>`;

// ---------------------------------------------------------------- home
async function vHome() {
  const [learn, books, changes, meta] = await Promise.all([store.load("learn"), store.load("textbooks"), store.load("changes").catch(() => ({ changes: [] })), store.load("meta")]);
  const classes = [...Array(12)].map((_, i) => i + 1);
  const quick = GROUPS.learn.filter((g) => g[0] !== "portals");
  const fresh = changes.changes.filter((c) => c.sec === "learn" && c.type !== "removed").slice(0, 5);
  let freshHtml;
  if (fresh.length) {
    freshHtml = fresh.map((c) => `<li><span class="badge ${c.type}">${esc(t(c.type === "new" ? "newBadge" : "updBadge"))}</span>
      <a href="${c.u ? esc(c.u) : "#/book/" + esc(c.i)}" ${c.u ? 'target="_blank" rel="noopener noreferrer"' : ""}>${esc(c.t)}</a>
      <span class="muted">${date(c.date)}</span></li>`).join("");
    freshHtml = `<ul class="plain">${freshHtml}</ul>`;
  } else {
    const upd = reg(learn.items.filter((x) => x.d && x.g !== "adult").sort((x, y) => (y.d > x.d ? 1 : -1)).slice(0, 4));
    freshHtml = `<p class="muted small">${esc(t("recentlyUpdated"))}</p><div class="list">${upd.map((x) => card(x, { hideNote: true })).join("")}</div>`;
  }
  const recent = store.recentItems();
  main.innerHTML = `
    <section class="hero">
      <h1>${esc(t("tagline"))}</h1>
      <form class="searchbar" role="search" data-form="search">
        <input type="search" name="q" placeholder="${esc(t("searchPh"))}" aria-label="${esc(t("search"))}">
        <button class="btn primary">${esc(t("search"))}</button>
      </form>
    </section>
    <section><h2>${esc(t("pickClass"))}</h2>
      <div class="classes">${classes.map((c) => `<a class="cls" href="#/class/${c}"><small>${esc(t("classN"))}</small>${c}</a>`).join("")}</div>
    </section>
    <section><h2>${esc(t("quick"))}</h2>${tiles(quick, (g) => (g[0] === "books" ? "#/books" : g[0] === "media" ? "#/videos" : `#/learn/${g[0]}`),
      (g) => (g[0] === "books" ? books.books.length : g[0] === "media" ? "" : learn.items.filter((x) => x.g === g[0]).length || ""))}</section>
    <section><div class="row-between"><h2>${esc(t("newForLearners"))}</h2><a href="#/new">${esc(t("allIn"))} ›</a></div>${freshHtml}</section>
    ${recent.length ? `<section><h2>${esc(t("recent"))}</h2><ul class="plain">${recent.slice(0, 6).map((r) =>
      `<li><a href="${esc(r.u)}" ${r.u.startsWith("#") ? "" : 'target="_blank" rel="noopener noreferrer"'}>${esc(titlePair(r)[0])}</a></li>`).join("")}</ul></section>` : ""}
    <p class="muted small center">${esc(t("synced"))}: ${esc(new Date(meta.synced).toLocaleString(lang() === "en" ? "en-IN" : "hi-IN"))}</p>`;
}

// ---------------------------------------------------------------- section landing pages
async function vSection(sec) {
  const data = await store.load(sec);
  const count = (g) => data.items.filter((x) => x.g === g[0]).length;
  const intro = { learn: t("learnIntro"), teach: t("teachIntro"), office: t("officeIntro") }[sec];
  let extra = "";
  if (sec === "learn") {
    const books = await store.load("textbooks");
    const groups = GROUPS.learn;
    main.innerHTML = head(t("learn"), intro) + tiles(groups, (g) => (g[0] === "books" ? "#/books" : g[0] === "media" ? "#/videos" : `#/learn/${g[0]}`),
      (g) => (g[0] === "books" ? books.books.length : g[0] === "media" ? "" : count(g) || ""));
    return;
  }
  if (sec === "teach") {
    const videos = await store.load("videos");
    const cols = videos.collections.filter((c) => c.sec === "teach");
    if (cols.length) extra = `<section><h2>🎬 ${esc(t("videos"))}</h2>${collectionsHtml(cols)}</section>`;
  }
  if (sec === "office") {
    const latest = reg(data.items.filter((x) => x.g === "notices" || x.g === "jobs").filter((x) => x.d).sort((a, b) => (b.d > a.d ? 1 : -1)).slice(0, 5));
    extra = `<section><h2>${esc(pick("ताज़ा सूचनाएँ व भर्ती", "Latest notices & jobs"))}</h2><div class="list">${latest.map((x) => card(x, { hideNote: true })).join("")}</div></section>`;
  }
  main.innerHTML = head(t(sec), intro) + tiles(GROUPS[sec].filter((g) => count(g)), (g) => `#/${sec}/${g[0]}`, count) + extra;
}

// ---------------------------------------------------------------- filtered list (any section/group)
async function vList(sec, g, preset = {}) {
  const data = await store.load(sec);
  const info = groupInfo(sec, g) || ["", "", g, g];
  const all = reg(data.items.filter((x) => x.g === g));
  const langs = [...new Set(all.flatMap((x) => x.l || []))];
  const kinds = [...new Set(all.map((x) => x.k))];
  const prods = [...new Set(all.map((x) => x.p).filter((p) => p && p !== "M"))];
  const classes = [...new Set(all.flatMap((x) => x.c || []))].sort((a, b) => a - b);
  const sel = (name, label, anyLabel, opts) => opts.length > 1 ? `<label><span class="vh">${esc(label)}</span><select name="${name}">
      <option value="">${esc(anyLabel)}</option>${opts.map(([v, l]) => `<option value="${esc(v)}">${esc(l)}</option>`).join("")}</select></label>` : "";
  main.innerHTML = head(pick(info[2], info[3]), info[4] ? pick(info[4], info[5]) : "", `#/${sec}`) + `
    <form class="filters" data-form="filter">
      <input type="search" name="q" placeholder="${esc(t("filterIn"))}" aria-label="${esc(t("filterIn"))}">
      ${sel("c", t("classN"), t("allClasses"), classes.map((c) => [c, `${t("classN")} ${c}`]))}
      ${sel("l", t("lang"), t("anyLang"), langs.map((l) => [l, pick(...(LANG_NAMES[l] || [l, l]))]))}
      ${sel("k", t("kind"), t("anyKind"), kinds.map((k) => [k, pick(KINDS[k][1], KINDS[k][2])]))}
      ${sel("p", t("product"), t("anyProduct"), prods.map((p) => [p, pick(PRODUCTS[p][1], PRODUCTS[p][2])]))}
      <label><span class="vh">${esc(t("sort"))}</span><select name="sort"><option value="">${esc(t("sortRel"))}</option>
        <option value="new">${esc(t("sortNew"))}</option><option value="az">${esc(t("sortAZ"))}</option></select></label>
    </form>
    <p class="count muted" id="count"></p><div class="list" id="list"></div>
    <div class="center"><button class="btn" data-act="more" id="moreBtn" hidden>${esc(t("more"))}</button></div>`;
  const form = main.querySelector("form");
  for (const [k, v] of Object.entries(preset)) if (form.elements[k]) form.elements[k].value = v;
  let shown = 0, view = [];
  const apply = () => {
    const f = Object.fromEntries(new FormData(form));
    const words = (f.q || "").toLowerCase().split(/\s+/).filter(Boolean);
    view = all.filter((x) => (!f.c || (x.c || []).includes(+f.c)) && (!f.l || (x.l || []).includes(f.l)) && (!f.k || x.k === f.k)
      && (!f.p || x.p === f.p) && words.every((w) => `${x.t} ${x.th || ""} ${x.n || ""} ${x.from ? x.from.join(" ") : ""}`.toLowerCase().includes(w)));
    if (f.sort === "new") view.sort((a, b) => ((b.d || "") > (a.d || "") ? 1 : -1));
    else if (f.sort === "az") view.sort((a, b) => titlePair(a)[0].localeCompare(titlePair(b)[0]));
    shown = 0;
    main.querySelector("#list").innerHTML = "";
    more();
  };
  const more = () => {
    const next = view.slice(shown, shown + PAGE);
    main.querySelector("#list").insertAdjacentHTML("beforeend", next.map((x) => card(x, { showProduct: sec === "learn" })).join("") ||
      (shown ? "" : `<p class="empty">${esc(t("none"))}</p>`));
    shown += next.length;
    main.querySelector("#count").textContent = `${view.length} ${t("items")}`;
    main.querySelector("#moreBtn").hidden = shown >= view.length;
  };
  form.addEventListener("input", apply);
  form.addEventListener("submit", (e) => e.preventDefault());
  main.querySelector("#moreBtn").onclick = more;
  apply();
}

// ---------------------------------------------------------------- textbooks
async function vBooks() {
  const { books } = await store.load("textbooks");
  const counts = {};
  for (const b of books) if (!b.h) counts[b.c] = (counts[b.c] || 0) + 1;
  const classes = Object.keys(counts).map(Number).sort((a, b) => a - b);
  main.innerHTML = head(t("textbooks"), pick("कक्षा चुनें, फिर विषय और किताब – हर अध्याय अलग से खोलें या पूरी किताब लें।",
    "Pick a class, then subject and book – open any chapter or get the whole book."), "#/learn") +
    `<div class="classes big">${classes.map((c) => `<a class="cls" href="#/books/${c}"><small>${esc(t("classN"))}</small>${esc(CLASS_LABEL(c))}
      <span class="cnt">${counts[c]} ${esc(t("books"))}</span></a>`).join("")}</div>`;
}

function bookCard(b) {
  const langs = b.v.map((v) => v.l).filter(Boolean);
  const ch = Math.max(...b.v.map((v) => v.ch.length));
  return `<a class="book" href="#/book/${esc(b.id)}"><span class="bt">${esc(b.t)}</span>
    <span class="bm">${ch ? `${ch} ${esc(t("chapters"))}` : ""}${langs.length ? ` · ${esc(langs.length > 3 ? `${langs.length} ${t("languages")}` : langs.join(", "))}` : ""}</span></a>`;
}

async function vBooksClass(c) {
  const { books } = await store.load("textbooks");
  const mine = books.filter((b) => b.c === c);
  const subjects = [...new Set(mine.map((b) => b.s))];
  main.innerHTML = head(`${t("textbooks")} · ${t("classN")} ${CLASS_LABEL(c)}`, "", "#/books") + subjects.map((s) => {
    const cur = mine.filter((b) => b.s === s && !b.h), old = mine.filter((b) => b.s === s && b.h);
    return `<section><h2>${esc(s)}</h2><div class="books">${cur.map(bookCard).join("")}</div>
      ${old.length ? `<details><summary>${esc(t("olderEditions"))} (${old.length})</summary><div class="books">${old.map(bookCard).join("")}</div></details>` : ""}</section>`;
  }).join("");
}

async function vBook(id, vi) {
  const { books, pdf_base } = await store.load("textbooks");
  const b = books.find((x) => x.id === id);
  if (!b) { main.innerHTML = `<p class="empty">${esc(t("none"))}</p>`; return; }
  const v = b.v[Math.min(+vi || 0, b.v.length - 1)];
  const url = (suffix) => `${pdf_base}${v.code}${suffix}`;
  const extra = { prelims: ["ps.pdf", t("prelims")], answers: ["an.pdf", t("answers")], appendix1: ["a1.pdf", `${t("appendix")} 1`], appendix2: ["a2.pdf", `${t("appendix")} 2`] };
  const row = (href, label) => `<li><a href="${esc(href)}" target="_blank" rel="noopener noreferrer" data-book="${esc(b.id)}">${esc(label)}</a></li>`;
  const item = { i: b.id, t: `${b.t} (${t("classN")} ${CLASS_LABEL(b.c)})`, u: `#/book/${b.id}`, k: "pdf", sec: "learn", g: "books" };
  REG.set(b.id, item);
  const saved = store.isSaved(b.id);
  main.innerHTML = head(b.t, `${t("classN")} ${CLASS_LABEL(b.c)} · ${b.s}${v.d ? ` · ${t("updated")} ${date(v.d)}` : ""}`, `#/books/${b.c}`) + `
    <div class="row-between">
      ${b.v.length > 1 ? `<div class="langtabs" role="tablist">${b.v.map((x, i) => `<a role="tab" aria-selected="${x === v}" class="chip${x === v ? " on" : ""}"
        href="#/book/${esc(b.id)}?v=${i}">${esc(x.l || "—")}</a>`).join("")}</div>` : "<span></span>"}
      <button class="btn star-btn${saved ? " on" : ""}" data-act="save" data-id="${esc(b.id)}" aria-pressed="${saved}">${saved ? "★" : "☆"} ${esc(saved ? t("saved") : t("save"))}</button>
    </div>
    <ol class="chapters">
      ${v.x.includes("prelims") ? row(url("ps.pdf"), t("prelims")) : ""}
      ${v.ch.map((n) => row(url(String(n).padStart(2, "0") + ".pdf"), `${t("chapter")} ${n}`)).join("")}
      ${Object.entries(extra).filter(([k]) => k !== "prelims" && v.x.includes(k)).map(([, [suf, label]]) => row(url(suf), label)).join("")}
    </ol>
    ${v.x.includes("book") ? `<p><a class="btn primary" href="${esc(url("dd.zip"))}" target="_blank" rel="noopener noreferrer">⬇ ${esc(t("wholeBook"))}</a></p>` : ""}
    <p class="muted small">${esc(t("online"))} – ${esc(pick("अध्याय NCERT की साइट से खुलते हैं। डाउनलोड करके 'मेरी शेल्फ़' में जोड़ें तो बिना इंटरनेट भी पढ़ सकते हैं।",
      "Chapters open from NCERT's site. Download one and add it under 'My shelf' to read it offline."))}</p>`;
}

async function vClass(c) {
  const [{ books }, learn] = await Promise.all([store.load("textbooks"), store.load("learn")]);
  const mine = books.filter((b) => (b.c === c || (b.c === 13 && c >= 11)) && !b.h);
  const items = learn.items.filter((x) => (x.c || []).includes(c) && x.g !== "adult");
  const byG = GROUPS.learn.map((g) => [g, items.filter((x) => x.g === g[0])]).filter(([, l]) => l.length);
  main.innerHTML = head(`${t("classN")} ${c}`, pick("इस कक्षा की किताबें और अभ्यास सामग्री", "Books and practice material for this class"), "#/") + `
    <section><h2>📚 ${esc(t("textbooks"))}</h2><div class="books">${mine.map(bookCard).join("") || `<p class="empty">${esc(t("none"))}</p>`}</div></section>
    ${byG.map(([g, l]) => `<section><div class="row-between"><h2>${g[1]} ${esc(pick(g[2], g[3]))}</h2>
      ${l.length > 6 ? `<a href="#/learn/${g[0]}?c=${c}">${esc(t("allIn"))} (${l.length}) ›</a>` : ""}</div>
      <div class="list">${reg(l.slice(0, 6)).map((x) => card(x, { hideNote: true })).join("")}</div></section>`).join("")}`;
}

// ---------------------------------------------------------------- videos
function collectionsHtml(cols) {
  return `<div class="list">${cols.map((c) => `<article class="card col">
    <div class="card-main"><h3 class="title">${esc(lang() === "hi" && c.th ? c.th : c.t)}</h3>
      ${c.n ? `<p class="note">${esc(c.n)}</p>` : ""}
      <div class="meta"><span>🎬 ${c.v.length} ${esc(t("videos"))}</span><span>${esc(c.ch || "")}</span></div>
      <div class="actions"><button class="btn primary" data-act="play-col" data-col="${esc(c.id)}">▶ ${esc(t("playAll"))}</button>
        ${c.page ? `<a class="btn" href="${esc(c.page)}" target="_blank" rel="noopener noreferrer">${esc(t("openPage"))}</a>` : ""}</div>
      <details><summary>${esc(pick("वीडियो सूची", "Video list"))}</summary><ol class="vlist">${c.v.map(([id, title], i) =>
        `<li><button class="linklike" data-act="play-col" data-col="${esc(c.id)}" data-start="${i}">▶ ${esc(title)}</button></li>`).join("")}</ol></details>
    </div></article>`).join("")}</div>`;
}

async function vVideos(sec) {
  const [videos, learn] = await Promise.all([store.load("videos"), store.load("learn")]);
  const files = reg(learn.items.filter((x) => x.g === "media"));
  const cols = videos.collections.filter((c) => c.sec === sec);
  main.innerHTML = head(t("videos"), t("videoNote"), "#/learn") + `
    <section><h2>${esc(t("channels"))}</h2><div class="tiles">${videos.channels.map((ch) => `
      <div class="tile"><span class="ico" aria-hidden="true">📺</span><span class="tl">${esc(ch.name)}</span>
        <span class="td">${ch.n ? `${ch.n} ${esc(pick("वीडियो NCERT साइट पर जुड़े", "videos linked on NCERT"))}` : ""}</span>
        <span class="actions"><button class="btn primary" data-act="play-list" data-list="${esc(ch.uploads)}" data-title="${esc(ch.name)}">▶ ${esc(t("playAll"))}</button>
        <a class="btn" href="${esc(ch.url)}" target="_blank" rel="noopener noreferrer">YouTube</a></span></div>`).join("")}</div></section>
    ${videos.playlists.length ? `<section><h2>${esc(pick("प्लेलिस्ट", "Playlists"))}</h2><div class="tiles">${videos.playlists.map((p) => `
      <div class="tile"><span class="ico" aria-hidden="true">🎞️</span><span class="tl">${esc(p.t)}</span>
      <span class="actions"><button class="btn primary" data-act="play-list" data-list="${esc(p.id)}" data-title="${esc(p.t)}">▶ ${esc(t("play"))}</button></span></div>`).join("")}</div></section>` : ""}
    <section><h2>${esc(t("collections"))}</h2>${collectionsHtml(cols)}</section>
    ${files.length ? `<section><h2>${esc(pick("NCERT पर रखी ऑडियो/वीडियो फ़ाइलें", "Audio/video files on NCERT"))}</h2>
      <div class="list">${files.map((x) => card(x, { hideNote: true })).join("")}</div></section>` : ""}`;
}

// ---------------------------------------------------------------- what's new
async function vNew(tab) {
  const { changes } = await store.load("changes").catch(() => ({ changes: [] }));
  const list = changes.filter((c) => (tab === "office" ? c.sec === "office" : c.sec !== "office"));
  const byDate = {};
  for (const c of list) (byDate[c.date] ||= []).push(c);
  if (changes[0]) store.markChangesSeen(changes[0].date);
  updateBadge();
  const label = { new: t("newBadge"), updated: t("updBadge"), removed: t("remBadge") };
  main.innerHTML = head(t("whatsnew"), pick("NCERT की साइट पर जो जुड़ा, बदला या हटा – अपने-आप दर्ज", "What NCERT added, changed or removed – recorded automatically")) + `
    <div class="langtabs" role="tablist">
      <a role="tab" class="chip${tab !== "office" ? " on" : ""}" aria-selected="${tab !== "office"}" href="#/new">${esc(t("forLearners"))}</a>
      <a role="tab" class="chip${tab === "office" ? " on" : ""}" aria-selected="${tab === "office"}" href="#/new?tab=office">${esc(t("forOffice"))}</a></div>
    ${Object.keys(byDate).length ? Object.entries(byDate).map(([d, cs]) => `<section><h2>${date(d)}</h2><ul class="plain changes">${cs.map((c) => `
      <li><span class="badge ${c.type}">${esc(label[c.type])}</span>
      ${c.type === "removed" || !(c.u || c.g === "textbooks") ? `<span>${esc(c.t)}</span>` :
        `<a href="${c.u ? esc(c.u) : "#/book/" + esc(c.i)}" ${c.u ? 'target="_blank" rel="noopener noreferrer"' : ""}>${esc(c.t)}</a>`}</li>`).join("")}</ul></section>`).join("")
      : `<p class="empty">${esc(t("noChanges"))}</p>`}`;
}

async function updateBadge() {
  try {
    const { changes } = await store.load("changes");
    const seen = store.lastSeenChanges();
    const n = changes.filter((c) => c.date > seen && c.sec !== "office").length;
    const el = document.getElementById("newCount");
    el.textContent = n > 99 ? "99+" : n;
    el.hidden = !n;
  } catch (e) { /* offline with nothing cached yet */ }
}

// ---------------------------------------------------------------- shelf (saved + offline PDFs)
async function vShelf() {
  const saved = store.shelfItems();
  reg(saved);
  let files = [];
  try { files = await store.listOfflineFiles(); } catch (e) { /* IndexedDB blocked */ }
  main.innerHTML = head(t("shelf")) + `
    <section><h2>★ ${esc(t("savedItems"))}</h2>${saved.length ? `<div class="list">${saved.map((x) => card(x)).join("")}</div>` : `<p class="empty">${esc(t("emptyShelf"))}</p>`}</section>
    <section><h2>📥 ${esc(t("myOffline"))}</h2><p class="muted">${esc(t("offlineHelp"))}</p>
      <label class="btn primary file"><input type="file" accept="application/pdf,.pdf" multiple data-act="add-files">＋ ${esc(t("addPdf"))}</label>
      <ul class="plain files">${files.map((f) => `<li><button class="linklike" data-act="open-file" data-fid="${f.id}">📄 ${esc(f.name)}</button>
        <span class="muted">${size(f.size)}</span><button class="btn small" data-act="del-file" data-fid="${f.id}">${esc(t("remove"))}</button></li>`).join("")}</ul></section>`;
}

// ---------------------------------------------------------------- search
async function vSearch(q) {
  main.innerHTML = head(t("search")) + `<form class="searchbar" role="search" data-form="search">
      <input type="search" name="q" value="${esc(q)}" placeholder="${esc(t("searchPh"))}" aria-label="${esc(t("search"))}" autofocus>
      <button class="btn primary">${esc(t("search"))}</button></form><div id="results"></div>`;
  if (!q.trim()) return;
  const res = await search(q);
  const books = res.filter((d) => d.type === "book").slice(0, 12);
  const cols = res.filter((d) => d.type === "collection").slice(0, 6);
  const items = res.filter((d) => d.type === "item");
  const bySec = ["learn", "teach", "office"].map((s) => [s, reg(items.filter((d) => d.it.sec === s).map((d) => d.it))]);
  main.querySelector("#results").innerHTML = `<p class="muted">${res.length} ${esc(t("results"))}</p>
    ${books.length ? `<section><h2>📚 ${esc(t("textbooks"))}</h2><div class="books">${books.map((d) => bookCard(d.b)).join("")}</div></section>` : ""}
    ${cols.length ? `<section><h2>🎬 ${esc(t("videos"))}</h2>${collectionsHtml(cols.map((d) => d.c))}</section>` : ""}
    ${bySec.filter(([, l]) => l.length).map(([s, l]) => `<section><h2>${esc(t(s))}</h2><div class="list">${l.slice(0, 30).map((x) => card(x)).join("")}</div></section>`).join("")}
    ${res.length ? "" : `<p class="empty">${esc(t("none"))}</p>`}`;
}

// ---------------------------------------------------------------- about & settings
async function vAbout() {
  const meta = await store.load("meta").catch(() => null);
  const s = store.settings;
  const radio = (name, val, label) => `<label class="chip${s[name] === val ? " on" : ""}"><input type="radio" name="${name}" value="${val}" ${s[name] === val ? "checked" : ""}>${esc(label)}</label>`;
  main.innerHTML = head(t("about")) + `
    <form class="settings" data-form="settings">
      <fieldset><legend>${esc(t("lang"))}</legend>${radio("lang", "hi", "हिंदी")}${radio("lang", "en", "English")}</fieldset>
      <fieldset><legend>${esc(t("theme"))}</legend>${radio("theme", "auto", t("themeAuto"))}${radio("theme", "light", t("themeLight"))}${radio("theme", "dark", t("themeDark"))}</fieldset>
    </form>
    <section class="prose"><h2>${esc(pick("यह ऐप क्या है", "What this app is"))}</h2>
      <p>${esc(pick("NCERT की वेबसाइट की हर सामग्री को शिक्षार्थी के नज़रिए से छाँटकर एक जगह – पढ़ाई की सामग्री 'सीखें' में, शिक्षकों की सामग्री अलग, और प्रशासनिक बातें 'कार्यालय' में। हर संसाधन एक ही बार दिखता है।",
        "Everything on NCERT's website, sorted from the learner's point of view – learning material under 'Learn', teachers' material separately, administration under 'Office'. Each resource appears once."))}</p>
      <p>${esc(pick("यह एक अनौपचारिक सूची है। सारी सामग्री NCERT की है और NCERT की साइट (ncert.nic.in) या YouTube से ही खुलती है – यह ऐप कोई फ़ाइल अपने पास नहीं रखता।",
        "This is an unofficial index. All content belongs to NCERT and opens from NCERT's site (ncert.nic.in) or YouTube – this app keeps no copies."))}</p>
      <h2>${esc(pick("अपडेट कैसे आते हैं", "How updates arrive"))}</h2>
      <p>${esc(pick("हर 6 घंटे में एक स्वचालित जाँच NCERT की साइट पढ़ती है – नई, बदली या हटाई गई सामग्री 'नया क्या है' में दिखती है और टूटी लिंक अपने-आप हट जाती हैं।",
        "Every 6 hours an automatic check reads NCERT's site – new, changed or removed material shows in 'What's new', and broken links are dropped automatically."))}</p>
      ${meta ? `<p class="muted">${esc(t("synced"))}: ${esc(new Date(meta.synced).toLocaleString(lang() === "en" ? "en-IN" : "hi-IN"))} ·
        ${meta.counts.learn + meta.counts.books} ${esc(pick("शिक्षार्थी सामग्री", "learner resources"))} · ${meta.counts.teach} ${esc(pick("शिक्षक सामग्री", "teacher resources"))} · ${meta.counts.office} ${esc(pick("कार्यालय", "office"))}</p>` : ""}
      <h2>${esc(pick("निजता", "Privacy"))}</h2>
      <ul>
        <li>${esc(pick("कोई खाता, कुकी, विज्ञापन या ट्रैकिंग नहीं।", "No accounts, cookies, ads or tracking."))}</li>
        <li>${esc(pick("सेव की गई चीज़ें, सेटिंग और ऑफ़लाइन PDF सिर्फ़ आपके डिवाइस में रहती हैं।", "Saved items, settings and offline PDFs stay on your device only."))}</li>
        <li>${esc(pick("YouTube तभी लोड होता है जब आप ▶ दबाते हैं (privacy-enhanced मोड)।", "YouTube loads only when you press ▶ (privacy-enhanced mode)."))}</li>
        <li>${esc(pick("यह ऐप GitHub Pages पर चलता है, जो सामान्य सर्वर लॉग (जैसे IP पता) रखता है – यह हमारे नियंत्रण में नहीं।", "The app is hosted on GitHub Pages, which keeps standard server logs (such as IP address) – outside our control."))}</li>
      </ul></section>`;
}

// ---------------------------------------------------------------- events (one delegated handler)
document.addEventListener("click", async (e) => {
  const act = e.target.closest("[data-act]");
  const open = e.target.closest("[data-open]");
  if (open && REG.has(open.dataset.open)) store.addRecent(REG.get(open.dataset.open));
  const bookLink = e.target.closest("[data-book]");
  if (bookLink && REG.has(bookLink.dataset.book)) store.addRecent(REG.get(bookLink.dataset.book));
  if (!act) return;
  const a = act.dataset.act;
  if (a === "save") {
    const it = REG.get(act.dataset.id);
    if (!it) return;
    const on = store.toggleSave(it);
    act.classList.toggle("on", on);
    act.setAttribute("aria-pressed", on);
    act.textContent = act.classList.contains("star-btn") ? `${on ? "★" : "☆"} ${on ? t("saved") : t("save")}` : on ? "★" : "☆";
    toast(on ? t("saved") : t("remove"));
  } else if (a === "close-player") closePlayer();
  else if (a === "play-list") playList(act.dataset.list, act.dataset.title);
  else if (a === "play-col") {
    const { collections } = await store.load("videos");
    const c = collections.find((x) => x.id === act.dataset.col);
    const start = +act.dataset.start || 0;
    if (c) playVideos(c.v.slice(start).concat(c.v.slice(0, start)).map((v) => v[0]), c.t);
  } else if (a === "open-file" || a === "del-file") {
    const id = +act.dataset.fid;
    if (a === "del-file") { await store.deleteOfflineFile(id); vShelf(); }
    else {
      const f = await store.getOfflineFile(id);
      if (f) window.open(URL.createObjectURL(f.blob), "_blank", "noopener");
    }
  }
});

document.addEventListener("change", async (e) => {
  if (e.target.matches('[data-act="add-files"]')) {
    for (const f of e.target.files) await store.addOfflineFile(f);
    toast(pick("PDF जोड़ी गई", "PDF added"));
    vShelf();
  }
  const sf = e.target.closest('[data-form="settings"]');
  if (sf) {
    const f = Object.fromEntries(new FormData(sf));
    store.settings.theme = f.theme;
    store.saveSettings();
    applyTheme();
    if (f.lang !== lang()) { setLang(f.lang); }
    render();
  }
});

document.addEventListener("submit", (e) => {
  if (e.target.matches('[data-form="search"]')) {
    e.preventDefault();
    const q = new FormData(e.target).get("q") || "";
    location.hash = `#/search?q=${encodeURIComponent(q)}`;
  }
});

document.addEventListener("keydown", (e) => { if (e.key === "Escape") closePlayer(); });
document.getElementById("langBtn").onclick = () => { setLang(lang() === "hi" ? "en" : "hi"); render(); };

window.addEventListener("hashchange", render);

const setOffline = () => document.body.classList.toggle("is-offline", !navigator.onLine);
window.addEventListener("online", setOffline);
window.addEventListener("offline", setOffline);

// ---------------------------------------------------------------- start
async function checkForUpdates() {
  try {
    const meta = await store.load("meta");
    const known = store.knownVersion();
    if (known && known !== meta.version) {
      store.forgetData();
      resetSearch();
      toast(t("updateReady"));
      render();
    }
    store.setKnownVersion(meta.version);
  } catch (e) { /* offline: keep using cached data */ }
  updateBadge();
}

applyTheme();
setOffline();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
render();
checkForUpdates();
