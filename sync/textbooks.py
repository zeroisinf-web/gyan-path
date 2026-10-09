"""NCERT textbooks, chapter-wise, read from the JavaScript menu inside https://ncert.nic.in/textbook.php

Usage:  python textbooks.py             parse the menu; verify chapter files only if the menu changed
        python textbooks.py --verify    re-verify every chapter file (HEAD requests)
Writes  state/textbooks_state.json  {menu_hash, books:[...], files:{url:{size,last_modified}}}

Each book: code, title, class, subject, chapters (N), hidden (commented out in NCERT's menu = older edition).
Chapter files follow NCERT's own naming:  textbook/pdf/<code>01.pdf … <code>NN.pdf,  <code>ps.pdf (prelims),
<code>dd.zip (whole book), <code>an.pdf / a1.pdf / a2.pdf (answers, appendices).
"""
import hashlib, json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor

import requests

import paths

BASE = "https://ncert.nic.in/"
PDF = BASE + "textbook/pdf/"
WORKERS = 6
EXTRA = [("ps.pdf", "prelims"), ("dd.zip", "book"), ("an.pdf", "answers"), ("a1.pdf", "appendix1"), ("a2.pdf", "appendix2")]
CLASS_NAMES = {13: "XI–XII", 14: "Vocational"}
LETTER_LANG = {"e": "English", "h": "Hindi", "u": "Urdu"}
LANGS = ["English", "Hindi", "Urdu", "Sanskrit", "Assamese", "Bengali", "Bodo", "Dogri", "Gujarati", "Kannada", "Kashmiri",
         "Konkani", "Maithili", "Malayalam", "Manipuri", "Marathi", "Nepali", "Odia", "Punjabi", "Santhali", "Sindhi",
         "Tamil", "Telugu"]
LANG_ALIASES = {"oriya": "Odia", "gujrati": "Gujarati", "maithli": "Maithili", "bangla": "Bengali", "santali": "Santhali"}

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def fetch_menu():
    for attempt in range(4):
        try:
            r = session.get(BASE + "textbook.php", timeout=60)
            r.raise_for_status()
            return r.text
        except requests.RequestException:
            time.sleep(5 * (attempt + 1))
    raise SystemExit("could not fetch textbook.php")


def language_of(title, code):
    m = re.search(r"\(([^)]+)\)\s*$", title or "")
    if m:
        word = m.group(1).strip().lower()
        word = LANG_ALIASES.get(word, word)
        for name in LANGS:
            if word == name.lower():
                return name, title[: m.start()].strip()
    return LETTER_LANG.get(code[1:2], ""), (title or "").strip()


def parse_books(js):
    """Book entries from the class/subject/book dropdown JavaScript."""
    cond = re.compile(r'tclass\.value\s*==\s*(\d+)\)\s*&&\s*\(document\.test\.tsubject\.options\[sind\]\.text\s*==\s*"([^"]+)"')
    opt_text = re.compile(r'tbook\.options\[(\d+)\]\.text\s*=\s*"([^"]*)"')
    opt_val = re.compile(r'tbook\.options\[(\d+)\]\.value\s*=\s*"textbook\.php\?([a-z0-9]+)=([0-9a-z]+)-([0-9]+)"', re.I)
    books, cls, subj, texts = {}, None, None, {}
    for line in js.splitlines():
        s = line.strip()
        hidden = s.startswith("//")
        m = cond.search(s)
        if m and not hidden:
            cls, subj, texts = int(m.group(1)), m.group(2), {}
            continue
        m = opt_text.search(s)
        if m:
            texts[(m.group(1), hidden)] = m.group(2)
            continue
        m = opt_val.search(s)
        if m:
            idx, code, start, end = m.groups()
            title = texts.get((idx, hidden)) or texts.get((idx, not hidden)) or ""
            b = books.get(code)
            if b is None or (b["hidden"] and not hidden):
                lang, base_title = language_of(title, code)
                books[code] = {"code": code, "title": title, "base_title": base_title, "lang": lang,
                               "class": cls, "class_name": CLASS_NAMES.get(cls, str(cls)), "subject": subj,
                               "chapters": int(end), "hidden": hidden,
                               "page": f"{BASE}textbook.php?{code}={start}-{end}"}
    return list(books.values())


def book_files(b):
    c = b["code"]
    files = [(f"{PDF}{c}{n:02d}.pdf", f"ch{n}") for n in range(1, b["chapters"] + 1)]
    files += [(f"{PDF}{c}{suf}", kind) for suf, kind in EXTRA]
    return files


def head(url):
    for attempt in range(3):
        try:
            r = session.head(url, timeout=40, allow_redirects=True)
            ct = (r.headers.get("Content-Type") or "").split(";")[0]
            if r.status_code == 200 and "html" not in ct:
                return url, {"size": r.headers.get("Content-Length"), "last_modified": r.headers.get("Last-Modified")}
            return url, None
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
    return url, "error"


def main():
    old = json.load(open(paths.TEXTBOOK_STATE, encoding="utf-8")) if os.path.exists(paths.TEXTBOOK_STATE) else {}
    js = fetch_menu()
    menu = js[js.find("function change1"):]          # the book list; ignore the rest of the page (dates, news…)
    menu_hash = hashlib.sha256(menu.encode("utf-8")).hexdigest()
    books = parse_books(js)
    print(f"books: {len(books)} (hidden/older: {sum(b['hidden'] for b in books)})", flush=True)
    if len(books) < 0.7 * len(old.get("books") or []):
        raise SystemExit("textbook menu shrank by more than 30% – NCERT page changed? keeping old data")

    files = dict(old.get("files") or {})
    if "--verify" in sys.argv or menu_hash != old.get("menu_hash") or not files:
        known = set(files) if "--verify" not in sys.argv else set()
        todo = [u for b in books for u, _ in book_files(b) if u not in known]
        print(f"verifying {len(todo)} files…", flush=True)
        t0 = time.time()
        with ThreadPoolExecutor(WORKERS) as ex:
            for i, (u, rec) in enumerate(ex.map(head, todo), 1):
                if rec == "error":
                    continue                 # network trouble: keep whatever we knew
                if rec:
                    files[u] = rec
                else:
                    files.pop(u, None)
                if i % 1000 == 0:
                    print(f"[{time.time()-t0:5.0f}s] {i}/{len(todo)}", flush=True)
    else:
        print("menu unchanged – files not re-verified", flush=True)

    state = {"menu_hash": menu_hash, "updated": int(time.time()), "books": books, "files": files}
    tmp = paths.TEXTBOOK_STATE + ".tmp"
    json.dump(state, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, paths.TEXTBOOK_STATE)
    have = sum(1 for b in books for u, _ in book_files(b) if u in files)
    print(f"DONE books={len(books)} files_available={have}", flush=True)


if __name__ == "__main__":
    main()
