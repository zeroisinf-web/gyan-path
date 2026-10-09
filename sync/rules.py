"""URL rules shared by crawl.py and build_report.py."""
import re
from urllib.parse import urlsplit


def excluded(u):
    """Individual book / e-book page URLs left out on request; their selector or cover pages are kept."""
    p = urlsplit(u)
    if p.hostname != "ncert.nic.in":
        return False
    path = p.path.lower()
    # book selectors (textbook.php, vocational.php, R3_learning_Resources.php …): drop per-book ?<code>=0-12 views
    if path.startswith("/textbook/pdf/") or (path.endswith(".php") and re.fullmatch(r"[a-z0-9_]+=[0-9a-z]+-[0-9]+", p.query, re.I)):
        return True
    # page-by-page files inside storybook e-books (Barkha series etc.): keep only each book's cover.html
    if "/ebooks/" in path and (p.query or not path.endswith("/cover.html")) and not path.endswith((".pdf", ".zip")):
        return True
    # internal files of a flipbook (per-page html, mobile view, swf): keep only the flipbook's own URL
    m = re.match(r"^/(flipbook[^/]*|comicflipbookenglish|gpepub)/[^/]+/(.*)$", path)
    if m and m.group(2) not in ("", "index.html", "index.htm"):
        return True
    return False
