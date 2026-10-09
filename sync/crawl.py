"""Crawl ncert.nic.in and collect every unique URL it links to.

Usage:  python crawl.py            resume an unfinished crawl in state/crawl_state.json
        python crawl.py --fresh    start a new crawl; the previous one is kept as state/crawl_state.prev.json
                                   (the scheduled sync uses --fresh so new and removed links are noticed)
"""
import json, os, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode, quote, unquote

import requests
from bs4 import BeautifulSoup

import paths
from rules import excluded

STATE = paths.CRAWL_STATE
PREV_STATE = os.path.join(paths.STATE, "crawl_state.prev.json")
ROOT = "https://ncert.nic.in/"
IN_SCOPE = {"ncert.nic.in"}
WORKERS = 8
MAX_PAGES = 20000
MAX_VARIANTS_PER_PATH = 300          # guard against query-string explosions
FILE_EXT = re.compile(r"\.(pdf|zip|rar|7z|docx?|xlsx?|pptx?|ppsx?|csv|txt|rtf|odt|jpe?g|png|gif|bmp|svg|webp|ico|"
                      r"mp4|mp3|wav|avi|mov|mkv|webm|flv|wmv|m4a|ogg|swf|apk|exe|epub|xml|json|css|js|woff2?|ttf|eot)$", re.I)
PAGE_EXT = re.compile(r"(\.(php|html?|aspx?|jsp)|/|/[^./]*)$", re.I)
JS_URL = re.compile(r"""(?:window\.open|location(?:\.href)?\s*=|location\.assign|location\.replace)\s*\(?\s*['"]([^'"]+)['"]""", re.I)
# quoted strings inside inline JS that look like site URLs, e.g. options[1].value="textbook.php?aemr1=0-9"
JS_STR_URL = re.compile(r"""['"]((?:https?://[^'"\s<>]+)|(?:[\w./-]+\.(?:php|html?|pdf|zip|docx?|pptx?|xlsx?|mp4)(?:\?[^'"\s<>]*)?))['"]""", re.I)
SKIP_SCHEMES =("javascript:", "mailto:", "tel:", "data:", "about:", "#", "whatsapp:", "sms:")

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) NCERT-link-inventory/1.0"
lock = threading.Lock()


def norm(raw, base):
    """Return (canonical_url, lang) or (None, None). lang is 'hi'/'en'/None from ?ln=."""
    if raw is None:
        return None, None
    raw = raw.strip().replace("\\", "/")
    if not raw or raw.lower().startswith(SKIP_SCHEMES):
        return None, None
    try:
        u = urlsplit(urljoin(base, raw))
    except ValueError:
        return None, None
    if u.scheme not in ("http", "https"):
        return None, None
    host = (u.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return None, None
    port = f":{u.port}" if u.port and u.port not in (80, 443) else ""
    path = re.sub(r"/{2,}", "/", u.path or "/")
    # resolve ../ and ./
    parts = []
    for seg in path.split("/"):
        if seg == "..":
            if len(parts) > 1:
                parts.pop()
        elif seg != ".":
            parts.append(seg)
    path = "/".join(parts) or "/"
    if not path.startswith("/"):
        path = "/" + path
    path = quote(unquote(path), safe="/%:@!$&'()*+,;=-._~")
    q = parse_qsl(u.query, keep_blank_values=True)
    lang = None
    kept = []
    for k, v in q:
        if k.lower() == "ln":
            lang = v.lower() or None
        else:
            kept.append((k, v))
    query = urlencode(sorted(kept))
    scheme = "https" if host in IN_SCOPE else u.scheme
    return urlunsplit((scheme, host + port, path, query, "")), lang


def in_scope(url):
    return urlsplit(url).hostname in IN_SCOPE


def is_page_candidate(url):
    u = urlsplit(url)
    if FILE_EXT.search(u.path):
        return False
    # every textbook.php?<bookcode>=a-b returns the same 570 KB JS page; textbooks.py handles those
    if u.path.lower() == "/textbook.php" and u.query:
        return False
    return True


def context(a, own_text):
    """Text around a link whose own text is short/generic ('PDF', 'View', 'हिंदी'): the other cells of its table
    row, or its list item / paragraph. This is usually the real title of the document."""
    row = a.find_parent("tr")
    if row is not None:
        cells = [c for c in row.find_all(["td", "th"], recursive=False) if a not in c.descendants]
        txt = " · ".join(c.get_text(" ", strip=True) for c in cells if c.get_text(strip=True))
    else:
        box = a.find_parent(["li", "p", "h1", "h2", "h3", "h4", "h5", "h6"]) or a.parent
        if box is not None and len(box.find_all("a")) > 2:
            # a line of many links ('Title – English || Hindi || Gujarati'): its label is the text before the first link
            first, lead = box.find("a"), []
            for node in box.descendants:
                if node is first:
                    break
                if isinstance(node, str):
                    lead.append(node)
            txt = " ".join(lead)
        else:
            txt = box.get_text(" ", strip=True) if box is not None else ""
            if own_text:
                txt = txt.replace(own_text, " ")
    txt = re.sub(r"\s+", " ", txt).strip(" |-–:·")
    return txt[:200] if len(txt) > len(own_text) + 2 else ""


def extract(html, base):
    soup = BeautifulSoup(html, "html.parser")
    b = soup.find("base", href=True)
    if b:
        base = urljoin(base, b["href"].strip())
    title = (soup.title.get_text(" ", strip=True) if soup.title else "")[:200]
    out = []
    for tag, attr in (("a", "href"), ("area", "href"), ("iframe", "src"), ("frame", "src"), ("embed", "src"),
                      ("object", "data"), ("source", "src"), ("video", "src"), ("audio", "src"), ("form", "action")):
        for el in soup.find_all(tag):
            v = el.get(attr)
            if not v:
                continue
            text = el.get_text(" ", strip=True) if tag == "a" else ""
            if not text and tag == "a":
                img = el.find("img")
                text = (img.get("alt") or img.get("title") or "") if img else (el.get("title") or "")
            text = re.sub(r"\s+", " ", text)[:150]
            out.append((v, text, tag, context(el, text) if tag == "a" and len(text) < 30 else ""))
    for el in soup.find_all(onclick=True):
        for m in JS_URL.finditer(el["onclick"]):
            out.append((m.group(1), el.get_text(" ", strip=True)[:150], "onclick", ""))
    for s in soup.find_all("script"):
        if s.string:
            for m in JS_URL.finditer(s.string):
                out.append((m.group(1), "", "script", ""))
            for m in JS_STR_URL.finditer(s.string):
                out.append((m.group(1), "", "script", ""))
    # embedded PDF links in option values (dropdown menus)
    for el in soup.find_all("option"):
        v = el.get("value") or ""
        if "/" in v and (FILE_EXT.search(v) or v.endswith(".php") or v.startswith("http")):
            out.append((v, el.get_text(" ", strip=True)[:150], "option", ""))
    return title, base, out


def load_state():
    if "--fresh" in sys.argv and os.path.exists(STATE):
        prev = json.load(open(STATE, encoding="utf-8"))
        if not prev.get("queue"):                 # only replace a finished crawl
            os.replace(STATE, PREV_STATE)
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"urls": {}, "queue": [ROOT], "done": []}


def main():
    st = load_state()
    urls = st["urls"]               # canonical -> record
    done = set(st["done"])
    queue = [u for u in st["queue"] if u not in done]
    queued = set(queue) | done
    edges = {(u, p) for u, r in urls.items() for p in r["found_on"]}
    path_variants = {}
    for u in queued:
        k = urlsplit(u).path
        path_variants[k] = path_variants.get(k, 0) + 1

    def rec(u):
        r = urls.get(u)
        if r is None:
            r = urls[u] = {"url": u, "texts": [], "found_on": [], "found_on_count": 0, "langs": [],
                           "status": None, "ctype": None, "title": None, "final_url": None, "via": []}
        return r

    rec(ROOT)["texts"].append("Home")

    def fetch(page):
        """Fetch English (default) + Hindi variants, return merged links."""
        results = {}
        for lang in (None, "hi"):
            fu = page + (("&" if "?" in page else "?") + "ln=hi" if lang else "")
            for attempt in range(3):
                try:
                    r = session.get(fu, timeout=40, allow_redirects=True, stream=True)
                    if "html" not in r.headers.get("Content-Type", "").lower():
                        r.close()   # binary/file: don't download the body
                    break
                except requests.RequestException as e:
                    err = str(e)[:120]
                    time.sleep(2 * (attempt + 1))
            else:
                results[lang] = {"error": err}
                continue
            ct = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
            d = {"status": r.status_code, "ctype": ct, "final": r.url}
            if r.status_code == 200 and "html" in ct:
                r.encoding = r.apparent_encoding if not r.encoding or r.encoding.lower() == "iso-8859-1" else r.encoding
                title, base, links = extract(r.text, r.url)
                d.update(title=title, base=base, links=links)
            results[lang] = d
            if "html" not in ct:   # not a page; no need for Hindi variant
                break
        return page, results

    pages_done = len(done)
    t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = {}
        while (queue or futs) and pages_done < MAX_PAGES:
            while queue and len(futs) < WORKERS * 2:
                p = queue.pop(0)
                futs[ex.submit(fetch, p)] = p
            fut = next(as_completed(futs))
            p = futs.pop(fut)
            page, res = fut.result()
            with lock:
                r = rec(page)
                en = res.get(None, {})
                r["status"] = en.get("status") or en.get("error")
                r["ctype"] = en.get("ctype")
                r["final_url"] = en.get("final") if en.get("final") and en.get("final").rstrip("/") != page.rstrip("/") else None
                r["title"] = en.get("title") or res.get("hi", {}).get("title")
                if "hi" in res and res["hi"].get("status") == 200:
                    r["has_hindi_page"] = True
                for lang, d in res.items():
                    for raw, text, tag, ctx in d.get("links", []):
                        cu, ln = norm(raw, d["base"])
                        if not cu or cu == page:
                            continue
                        t = rec(cu)
                        if text and text not in t["texts"] and len(t["texts"]) < 8:
                            t["texts"].append(text)
                        if ctx and ctx not in t.setdefault("ctx", []) and len(t["ctx"]) < 3:
                            t["ctx"].append(ctx)
                        if (cu, page) not in edges:
                            edges.add((cu, page))
                            t["found_on_count"] += 1
                            t["found_on"].append(page)
                        if ln and ln not in t["langs"]:
                            t["langs"].append(ln)
                        if tag not in t["via"]:
                            t["via"].append(tag)
                        if in_scope(cu) and is_page_candidate(cu) and cu not in queued and not excluded(cu):
                            k = urlsplit(cu).path
                            if path_variants.get(k, 0) < MAX_VARIANTS_PER_PATH:
                                path_variants[k] = path_variants.get(k, 0) + 1
                                queued.add(cu)
                                queue.append(cu)
                done.add(page)
                pages_done += 1
                if pages_done % 50 == 0:
                    print(f"[{time.time()-t0:6.0f}s] pages={pages_done} queue={len(queue)} urls={len(urls)}", flush=True)
                if pages_done % 200 == 0:
                    save(urls, queue + list(futs.values()), done)
    save(urls, queue + list(futs.values()), done)
    print(f"DONE pages={pages_done} queue_left={len(queue)} unique_urls={len(urls)}", flush=True)


def save(urls, queue, done):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"urls": urls, "queue": queue, "done": sorted(done)}, f, ensure_ascii=False)
    os.replace(tmp, STATE)


if __name__ == "__main__":
    main()
