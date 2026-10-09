// Offline search across every section, textbooks and video collections. Works in Hindi and English.
import { load } from "./store.js";

let index = null;

const norm = (s) =>
  String(s || "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^\p{L}\p{N}\p{M}]+/gu, " ")
    .trim();

// words hidden in NCERT's file paths, e.g. /exemplarproblem/classX/mathematics/ -> "exemplarproblem class x mathematics"
function pathWords(u) {
  try {
    return decodeURIComponent(new URL(u).pathname).replace(/class(?=[ivx\d])/gi, "class ").replace(/[\/_\-.%]+/g, " ");
  } catch (e) {
    return "";
  }
}

// "maths" should find "mathematics", "books" should find "book"
const variants = (w) => (w.length > 4 && w.endsWith("s") ? [w, w.slice(0, -1)] : [w]);

async function build() {
  const [learn, teach, office, books, videos] = await Promise.all(
    ["learn", "teach", "office", "textbooks", "videos"].map((n) => load(n).catch(() => null)));
  const docs = [];
  for (const sec of [learn, teach, office]) {
    for (const it of sec?.items || []) {
      const from = it.from ? it.from[0] + " " + it.from[1] : "";
      const cls = (it.c || []).map((c) => `class ${c} कक्षा ${c}`).join(" ");
      docs.push({ type: "item", it, head: norm(it.t + " " + (it.th || "")), body: norm([it.n, it.s, from, cls, pathWords(it.u)].join(" ")) });
    }
  }
  for (const b of books?.books || []) {
    const langs = b.v.map((v) => v.l).join(" ");
    docs.push({ type: "book", b, head: norm(b.t + " " + b.s), body: norm(`class ${b.c} कक्षा ${b.c} ${b.cn} ${langs} textbook पाठ्यपुस्तक`) });
  }
  for (const c of videos?.collections || []) {
    docs.push({ type: "collection", c, head: norm(c.t + " " + (c.th || "")), body: norm(c.n + " " + c.v.map((v) => v[1]).join(" ")) });
  }
  index = docs;
}

const ROMAN = { i: 1, ii: 2, iii: 3, iv: 4, v: 5, vi: 6, vii: 7, viii: 8, ix: 9, x: 10, xi: 11, xii: 12 };
const CLASS_IN_QUERY = /(?:^|\s)(?:class|grade|कक्षा)\s*(1[0-2]|[1-9]|xii|xi|ix|x|viii|vii|vi|iv|v|iii|ii|i)(?=\s|$)/i;

// "class 10" / "कक्षा 10" in a query is a filter, not two words to match
function classOf(d) {
  if (d.type === "item") return d.it.c || [];
  if (d.type === "book") return d.b.c === 13 ? [11, 12] : [d.b.c];
  return [];
}

export async function search(q, limit = 120) {
  if (!index) await build();
  let text = norm(q), cls = null;
  const m = text.match(CLASS_IN_QUERY);
  if (m) {
    cls = ROMAN[m[1].toLowerCase()] || +m[1];
    text = text.replace(m[0], " ");
  }
  const words = text.split(" ").filter(Boolean);
  if (!words.length && !cls) return [];
  const out = [];
  for (const d of index) {
    if (cls && !classOf(d).includes(cls)) continue;
    let score = 0, ok = true;
    for (const word of words) {
      const vs = variants(word);
      if (vs.some((w) => d.head.includes(w))) score += vs.some((w) => d.head.startsWith(w)) ? 4 : 3;
      else if (vs.some((w) => d.body.includes(w))) score += 1;
      else { ok = false; break; }
    }
    if (ok) out.push([score + (d.type === "book" ? 2 : 0), d]);
  }
  out.sort((a, b) => b[0] - a[0]);
  return out.slice(0, limit).map((x) => x[1]);
}

export const resetSearch = () => { index = null; };
