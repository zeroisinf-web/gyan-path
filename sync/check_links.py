"""Check every non-page URL from the crawl (files + external links) with lightweight HEAD requests.

Usage:  python check_links.py            new URLs + the oldest 1/7 of known ones (weekly rotation)
        python check_links.py --all      re-check everything
Writes  state/link_status.json:  url -> {status, final, host, last_modified, size, checked}
'last_modified' / 'size' come from NCERT's Last-Modified / Content-Length headers and are how export.py
notices that a file was replaced (shown in the app's "What's new").
"""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlsplit

import requests

import paths
from rules import excluded

WORKERS = 12
ROTATE_DAYS = 7


def check(session, u):
    last = None
    for attempt in range(3):
        try:
            r = session.head(u, timeout=30, allow_redirects=True)
            if r.status_code >= 400:
                # many servers reject HEAD; confirm with a GET that stops after the headers
                r = session.get(u, timeout=30, allow_redirects=True, stream=True)
                r.close()
            h = r.headers
            return u, {"status": r.status_code, "final": r.url if r.url != u else None,
                       "last_modified": h.get("Last-Modified"), "size": h.get("Content-Length"),
                       "type": (h.get("Content-Type") or "").split(";")[0] or None}
        except requests.exceptions.ConnectionError as e:
            last = "dns/connection error" if "NameResolution" in str(e) or "getaddrinfo" in str(e) else "connection error"
        except requests.RequestException as e:
            last = type(e).__name__
        time.sleep(2 * (attempt + 1))
    return u, {"status": last, "final": None}


def run(urls, status, label="links"):
    """HEAD-check `urls`, updating `status` in place and saving every 500."""
    session = requests.Session()
    session.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                     "(KHTML, like Gecko) Chrome/120 Safari/537.36")
    t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = [ex.submit(check, session, u) for u in urls]
        for i, f in enumerate(as_completed(futs), 1):
            u, rec = f.result()
            rec["host"] = urlsplit(u).hostname
            rec["checked"] = int(time.time())
            old = status.get(u) or {}
            # a temporary failure must not wipe what we knew about a working file
            if not isinstance(rec["status"], int) and isinstance(old.get("status"), int):
                rec = dict(old, last_error=rec["status"], checked=rec["checked"])
            status[u] = rec
            if i % 500 == 0:
                print(f"[{time.time()-t0:5.0f}s] {label}: {i}/{len(urls)}", flush=True)
                save(status)
    save(status)


def save(status):
    tmp = paths.LINK_STATUS + ".tmp"
    json.dump(status, open(tmp, "w", encoding="utf-8"))
    os.replace(tmp, paths.LINK_STATUS)


def main():
    st = json.load(open(paths.CRAWL_STATE, encoding="utf-8"))
    pages = set(st["done"])
    status = json.load(open(paths.LINK_STATUS, encoding="utf-8")) if os.path.exists(paths.LINK_STATUS) else {}
    wanted = [u for u in st["urls"] if u not in pages and not excluded(u)]
    new = [u for u in wanted if u not in status]
    if "--all" in sys.argv:
        due = [u for u in wanted if u in status]
    else:
        known = sorted((u for u in wanted if u in status), key=lambda u: status[u].get("checked", 0))
        cutoff = time.time() - ROTATE_DAYS * 86400
        due = [u for u in known if status[u].get("checked", 0) < cutoff][: max(1, len(known) // ROTATE_DAYS)]
    print(f"new: {len(new)}  re-check: {len(due)}  (known: {len(status)})", flush=True)
    run(new + due, status)
    print("DONE", len(status), flush=True)


if __name__ == "__main__":
    main()
