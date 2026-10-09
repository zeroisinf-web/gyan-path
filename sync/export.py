"""Write the web app's data files (data/*.json) from the crawl, link checks, textbooks and YouTube state.

Usage:  python export.py
Writes  data/meta.json        version, sync time, counts
        data/learn.json       direct-to-learner products (student lens groups 1-2)
        data/teach.json       for teachers / parents / volunteers (group 3)
        data/office.json      system & research (4), news (5), administration (6), other links (7)
        data/textbooks.json   class -> subject -> book (+ language versions) -> available chapters
        data/videos.json      channels (embeddable uploads list) + collections (NCERT pages' videos as one playlist)
        data/changes.json     what's new: new / updated / removed items, last 90 days
        state/history.json    first-seen date and file signature per item (feeds changes.json)
Refuses to publish (exit 2) when the catalogue shrank by more than 30% – usually NCERT's site changed shape.
"""
import collections, datetime, hashlib, html, json, os, re, sys, time
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, unquote

import paths
import student_lens
import dedupe
from catalog import Catalog
from youtube import parse_youtube
from textbooks import book_files

TODAY = datetime.date.today().isoformat()
KEEP_CHANGES_DAYS = 90
ROLE_KEY = {v: k for k, v in student_lens.ROLE.items()}
PROD = {"Knowledge": "K", "Skill": "S", "Thinking & creativity": "T", "Career, money & opportunity": "C",
        "Wellbeing & safety": "W", student_lens.MIXED: "M"}
SECTION_OF_ROLE = {"D": "learn", "G": "learn", "T": "teach", "S": "office", "P": "office", "O": "office", "X": "office"}


def iid(url):
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]


def kind_of(row):
    t, path = row["Type"], urlsplit(row["URL"]).path.lower()
    if t == "PDF":
        return "pdf"
    if t in ("Word", "Excel", "PowerPoint", "Text"):
        return "doc"
    if t.startswith("Archive"):
        return "zip"
    if t.startswith("e-Book"):
        return "epub"
    if t == "Image":
        return "img"
    if t == "Audio/Video":
        return "audio" if re.search(r"\.(mp3|wav|m4a|ogg)$", path) else "video"
    if t == "Flipbook":
        return "flip"
    if t == "External link":
        return "link"
    return "page"


def learn_group(row, kind, path, prod, hay):
    if path.startswith("/cncl/") or "/adulteducation" in path or "ullas" in hay:
        return "adult"
    if kind in ("video", "audio") or re.search(r"/(video|audio)s?/|_(video|audio)_program", path):
        return "media"
    if "competition / opportunity" in row["What it is / used for"] or re.search(
            r"ntse|talent.?search|rbvp|bal.?vaigyanik|kala.?utsav|prayaas|olympiad|competition|प्रतियोगिता", hay):
        return "opportunity"
    if kind in ("flip", "epub") or re.search(r"/ebooks/|barkhaseries|tamanna|jaadui|flipbook|e-?comic|interactive", hay):
        return "interactive"
    if kind == "link":
        return "portals"
    if prod == "T":
        return "practice"
    if prod in ("W", "C"):
        return "wellbeing"
    if prod == "S":
        return "skills"
    return "read"


def teach_group(topic, hay):
    if re.search(r"journal|magazine|पत्रिका", hay):
        return "journals"
    if topic in ("Teacher Education & Training", "Admissions & Courses") or re.search(r"training|course|प्रशिक्षण", hay):
        return "training"
    if topic in ("Exams, Olympiads & Assessment", "Curriculum, Syllabus & Policy") or re.search(r"assess|outcome|syllabus|cce|hpc", hay):
        return "assessment"
    if topic == "Events, Competitions & Days" or re.search(r"seminar|webinar|workshop|conference|lecture", hay):
        return "events"
    return "guides"


def office_group(role, topic):
    if role == "S":
        return "system"
    if role == "P":
        return "news"
    if role == "X":
        return "links"
    return {"Recruitment & Vacancies": "jobs", "Tenders & Procurement": "tenders", "Notices, Circulars & Orders": "notices",
            "Pension, Insurance & Accounts": "accounts"}.get(topic, "about")


def iso_date(http_date):
    try:
        return parsedate_to_datetime(http_date).date().isoformat()
    except Exception:
        return None


def app_note(note):
    """The report's 'what it is for' note, minus the analysis wording. 'Item listed on /x.php – Exemplar Problems – …'
    keeps only the useful part; notes that only describe the listing page ('Shelf of…', 'Home page…') are dropped,
    because the card's 'from' line already says where the item comes from."""
    n = re.sub(r"^(?:YouTube video\. )?(?:Item|Video|Link) listed on \S+(?: – )?", "", note or "").strip()
    if not n or re.match(r"(?i)(shelf of|home page of|ncert home page|page on the ncert site|archive of|list of the department|"
                         r"staff of|office staff|contact details|faculty of|publications of this unit)", n):
        return ""
    return n


def build_items(cat):
    status = cat.link_status
    items = []
    for row in cat.rows:
        url, role = row["URL"], ROLE_KEY[row["Reaches learner"]]
        p = urlsplit(url)
        path, host = unquote(p.path).lower(), p.hostname or ""
        kind = kind_of(row)
        if parse_youtube(url):
            continue                                   # videos come from videos.json (channels / collections)
        if kind == "img" and role not in ("D", "T"):
            continue                                   # event photos: the gallery pages are listed instead
        rec = cat.urls.get(url) or {}
        texts = rec.get("texts") or []
        parents = [x for x in rec.get("found_on") or [] if x in cat.urls]
        parent = min(parents, key=lambda x: (cat.urls[x].get("found_on_count", 0), len(x))) if parents else None
        en, hi = dedupe.titles(url, texts, rec.get("ctx"), rec.get("title") or "")
        prod = PROD.get(row["Eventual product for learner"], "")
        hay = " ".join([path, " ".join(texts), row["What it is / used for"]]).lower()
        sec = SECTION_OF_ROLE[role]
        grp = (learn_group(row, kind, path, prod, hay) if sec == "learn"
               else teach_group(row["Topic"], hay) if sec == "teach" else office_group(role, row["Topic"]))
        ls = status.get(url) or {}
        size = ls.get("size")
        it = {"i": iid(url), "u": url, "t": en, "th": hi, "n": app_note(row["What it is / used for"]), "k": kind, "p": prod,
              "sec": sec, "g": grp, "s": row["Section"], "l": dedupe.languages(url, texts),
              "c": dedupe.classes(url, texts), "z": int(size) if size and str(size).isdigit() else None,
              "d": iso_date(ls.get("last_modified")), "r": row["Linked from (pages)"],
              "pp": parent if kind != "page" and parent and parent.rstrip("/") not in ("https://ncert.nic.in", "https://ncert.nic.in/index.php") else None,
              # only NCERT's own files are tracked for "updated": outside sites and web pages report a
              # new Last-Modified on every visit, which would flood What's new
              "_sig": (f"{ls.get('last_modified')}|{size}"
                       if host == "ncert.nic.in" and kind not in ("page", "link") and (ls.get("last_modified") or size) else None)}
        if not it["t"] and not it["th"]:
            it["t"] = dedupe.from_filename(url) or host
        items.append(it)
    return items


def merge_duplicates(items):
    """1) same file at two paths -> one item;  2) English/Hindi/Urdu copies of one document -> one item with versions."""
    by_file = collections.defaultdict(list)
    for it in items:
        k = dedupe.same_file_key(it["u"], it["z"]) if it["k"] not in ("page", "link") else None
        if k:
            by_file[k].append(it)
    drop = set()
    for group in by_file.values():
        if len(group) > 1:
            keep = max(group, key=lambda x: (x["r"], -len(x["u"])))
            keep["a"] = [x["u"] for x in group if x is not keep]
            drop.update(id(x) for x in group if x is not keep)
    items = [x for x in items if id(x) not in drop]

    by_lang = collections.defaultdict(list)
    for it in items:
        if it["k"] not in ("page", "link") and it["l"]:
            by_lang[(it["sec"], it["g"], dedupe.lang_key(it["u"]))].append(it)
    drop = set()
    for group in by_lang.values():
        langs = {x["l"][0] for x in group}
        if len(group) > 1 and len(langs) == len(group):
            order = {"en": 0, "hi": 1, "ur": 2}
            group.sort(key=lambda x: order.get(x["l"][0], 9))
            main = group[0]
            main["v"] = [{"l": x["l"][0], "u": x["u"], "z": x["z"]} for x in group]
            main["l"] = [x["l"][0] for x in group]
            main["th"] = main["th"] or next((x["th"] for x in group if x["th"]), "")
            drop.update(id(x) for x in group[1:])
    return [x for x in items if id(x) not in drop]


def build_textbooks():
    if not os.path.exists(paths.TEXTBOOK_STATE):
        return {"books": []}
    st = json.load(open(paths.TEXTBOOK_STATE, encoding="utf-8"))
    files = st.get("files") or {}
    cards = {}
    for b in st["books"]:
        avail = {kind for u, kind in book_files(b) if u in files}
        chapters = sorted(int(k[2:]) for k in avail if k.startswith("ch"))
        if not chapters and "book" not in avail:
            continue                                         # nothing downloadable for this book
        m = re.search(r"\(([^)]+)\)\s*$", b["title"])
        key = (b["class"], b["subject"], b["base_title"].lower()) if m else (b["class"], b["code"][0] + b["code"][2:])
        card = cards.setdefault(key, {"id": "b-" + b["code"], "t": b["base_title"], "c": b["class"], "cn": b["class_name"],
                                      "s": b["subject"], "h": b["hidden"], "v": []})
        card["h"] = card["h"] and b["hidden"]
        if b["lang"] == "English" or not card["t"]:
            card["t"] = b["base_title"]
        card["v"].append({"l": b["lang"] or "", "code": b["code"], "ch": chapters,
                          "x": sorted(k for k in avail if not k.startswith("ch")),
                          "d": max((iso_date(files[u].get("last_modified")) or "" for u, _ in book_files(b) if u in files),
                                   default="") or None})
    order = {"English": 0, "Hindi": 1, "Urdu": 2}
    books = sorted(cards.values(), key=lambda c: (c["c"], c["s"], c["h"], c["t"]))
    for c in books:
        c["v"].sort(key=lambda v: (order.get(v["l"], 5), v["l"]))
    return {"pdf_base": "https://ncert.nic.in/textbook/pdf/", "books": books}


def build_videos(cat):
    if not os.path.exists(paths.YOUTUBE_STATE):
        return {"channels": [], "collections": [], "playlists": []}
    st = json.load(open(paths.YOUTUBE_STATE, encoding="utf-8"))
    vids, chans = st["videos"], st["channels"]
    pages = collections.defaultdict(list)
    per_channel = collections.Counter()
    seen = set()
    for row in cat.rows:
        y = parse_youtube(row["URL"])
        if not y or y[0] != "video":
            continue
        vid = y[1]
        v = vids.get(vid)
        if not v or not v.get("ok") or vid in seen:
            continue
        seen.add(vid)
        per_channel[v.get("channel_url")] += 1
        rec = cat.urls.get(row["URL"]) or {}
        parents = [x for x in rec.get("found_on") or [] if x in cat.urls]
        parent = min(parents, key=lambda x: (cat.urls[x].get("found_on_count", 0), len(x))) if parents else ""
        pages[parent].append((vid, v.get("title") or "", v.get("channel")))
    rows_by_url = {r["URL"]: r for r in cat.rows}
    collections_out = []
    for page, vlist in pages.items():
        prow = rows_by_url.get(page) or {}
        prec = cat.urls.get(page) or {}
        pt = dedupe.text_parts(prec.get("texts"))
        en = next((x for x in pt if not dedupe.DEVANAGARI.search(x)), "") or (prec.get("title") or "")
        hi = next((x for x in pt if dedupe.DEVANAGARI.search(x)), "")
        role = ROLE_KEY.get(prow.get("Reaches learner", ""), "D")
        collections_out.append({
            "id": "c-" + iid(page or "misc"), "t": en or "More videos", "th": hi, "page": page,
            "n": prow.get("What it is / used for", ""), "sec": "teach" if role == "T" else ("office" if role in "SPOX" else "learn"),
            "p": PROD.get(prow.get("Eventual product for learner", ""), ""),
            "ch": collections.Counter(c for _, _, c in vlist).most_common(1)[0][0],
            "v": [[vid, title] for vid, title, _ in vlist]})
    collections_out.sort(key=lambda c: -len(c["v"]))
    merged = {}                                     # one channel can be linked as /@handle and as /channel/UC…
    for url, c in chans.items():
        m = merged.setdefault(c["uploads"], {"name": html.unescape(c.get("name") or url.rsplit("/", 1)[-1]),
                                             "url": url, "uploads": c["uploads"], "n": 0})
        m["n"] += per_channel.get(url, 0)
        if "/@" in url:
            m["url"] = url
    channels_out = sorted(merged.values(), key=lambda c: -c["n"])
    playlists = [{"id": pid, "t": p.get("title") or "Playlist", "ch": p.get("channel_url")} for pid, p in st["playlists"].items()]
    return {"channels": channels_out, "collections": collections_out, "playlists": playlists}


def is_ncert_file(url):
    """A file on ncert.nic.in (not a page). Textbook changes have no url and always count."""
    if not url:
        return True
    p = urlsplit(url)
    return p.hostname == "ncert.nic.in" and bool(re.search(r"\.[a-z0-9]{2,4}$", p.path.lower())) \
        and not re.search(r"\.(php|html?)$", p.path.lower())


def update_history(items, textbooks):
    """first-seen dates + file signatures -> changes feed. The very first run is a silent baseline."""
    hist = json.load(open(paths.HISTORY, encoding="utf-8")) if os.path.exists(paths.HISTORY) else None
    baseline = hist is None
    hist = hist or {"items": {}, "changes": []}
    known = hist["items"]
    current = {}
    for it in items:
        current[it["i"]] = {"sig": it.get("_sig"), "t": it["t"] or it["th"], "u": it["u"], "sec": it["sec"], "g": it["g"]}
    for b in textbooks["books"]:
        sig = "|".join(f"{v['code']}:{len(v['ch'])}:{v['d']}" for v in b["v"])
        current[b["id"]] = {"sig": sig, "t": f"{b['t']} (Class {b['cn']})", "u": None, "sec": "learn", "g": "textbooks"}
    changes = hist["changes"]
    if not baseline:
        for k, cur in current.items():
            old = known.get(k)
            if old is None:
                changes.append({"i": k, "type": "new", "date": TODAY, **{x: cur[x] for x in ("t", "u", "sec", "g")}})
            elif cur["sig"] and old.get("sig") and cur["sig"] != old["sig"]:
                changes.append({"i": k, "type": "updated", "date": TODAY, **{x: cur[x] for x in ("t", "u", "sec", "g")}})
        for k, old in known.items():
            if k not in current and not old.get("gone"):
                changes.append({"i": k, "type": "removed", "date": TODAY, **{x: old.get(x) for x in ("t", "u", "sec", "g")}})
    for k, cur in current.items():
        prev = known.get(k, {})
        known[k] = {**cur, "first": prev.get("first") or (None if baseline else TODAY)}
    for k in list(known):
        if k not in current:
            known[k]["gone"] = known[k].get("gone") or TODAY
    cutoff = (datetime.date.today() - datetime.timedelta(days=KEEP_CHANGES_DAYS)).isoformat()
    hist["changes"] = [c for c in changes if c["date"] >= cutoff and (c["type"] != "updated" or is_ncert_file(c.get("u")))]
    hist["items"] = {k: v for k, v in known.items() if not v.get("gone") or v["gone"] >= cutoff}
    tmp = paths.HISTORY + ".tmp"
    json.dump(hist, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, paths.HISTORY)
    return hist, baseline


def write(name, obj):
    tmp = os.path.join(paths.DATA, name + ".tmp")
    json.dump(obj, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, os.path.join(paths.DATA, name))


def drop_shelves(items):
    """A page that is the source of 3+ listed items is just a shelf: its items are already listed one by one,
    so the page itself only shows up as their 'from' line. Lists are then ordered by how widely NCERT links them."""
    listed_from = collections.Counter(it["pp"] for it in items if it.get("pp"))
    kept = [it for it in items if not (it["k"] == "page" and listed_from.get(it["u"], 0) >= 3)]
    kept.sort(key=lambda it: (it["sec"], it["g"], -(it["r"] or 0), (it["t"] or it["th"]).lower()))
    return kept


def main():
    cat = Catalog()
    items = drop_shelves(merge_duplicates(build_items(cat)))
    textbooks = build_textbooks()
    videos = build_videos(cat)

    meta_path = os.path.join(paths.DATA, "meta.json")
    old_meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}
    total = len(items) + len(textbooks["books"])
    if old_meta.get("total") and total < 0.7 * old_meta["total"]:
        print(f"REFUSING to publish: {total} items vs {old_meta['total']} last time (NCERT site changed?)", flush=True)
        sys.exit(2)

    hist, baseline = update_history(items, textbooks)
    first = {k: v.get("first") for k, v in hist["items"].items()}
    by_sec = collections.defaultdict(list)
    pages = collections.defaultdict(dict)           # per section: parent-page id -> [title, alt title, url]
    for it in items:
        it["f"] = first.get(it["i"])
        it.pop("_sig", None)
        it.pop("r", None)
        pu = it.pop("pp", None)
        if pu:
            pid = iid(pu)
            if pid not in pages[it["sec"]]:
                prec = cat.urls.get(pu) or {}
                t, th = dedupe.titles(pu, prec.get("texts"), prec.get("ctx"), prec.get("title") or "")
                pages[it["sec"]][pid] = [t, th, pu]
            it["pp"] = pid
        by_sec[it["sec"]].append({k: v for k, v in it.items() if v not in (None, "", []) and k != "sec"})
    for sec in ("learn", "teach", "office"):
        # notes ('n') and section names ('s') repeat thousands of times: store each once, items keep an index
        notes, sections = {}, {}
        for it in by_sec[sec]:
            if "n" in it:
                it["n"] = notes.setdefault(it["n"], len(notes))
            if "s" in it:
                it["s"] = sections.setdefault(it["s"], len(sections))
        write(f"{sec}.json", {"notes": list(notes), "sections": list(sections), "pages": pages[sec], "items": by_sec[sec]})
    write("textbooks.json", textbooks)
    write("videos.json", videos)
    write("changes.json", {"changes": sorted(hist["changes"], key=lambda c: c["date"], reverse=True)})

    payload = "".join(open(os.path.join(paths.DATA, f), encoding="utf-8").read()
                      for f in ("learn.json", "teach.json", "office.json", "textbooks.json", "videos.json"))
    meta = {"version": hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12],
            "synced": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="minutes"),
            "data_changed": old_meta.get("data_changed") if old_meta.get("version") == hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12] else TODAY,
            "total": total, "source": "https://ncert.nic.in/",
            "counts": {"learn": len(by_sec["learn"]), "teach": len(by_sec["teach"]), "office": len(by_sec["office"]),
                       "books": len(textbooks["books"]), "collections": len(videos["collections"]),
                       "channels": len(videos["channels"]), "removed_broken": len(cat.removed)}}
    write("meta.json", meta)
    print(f"{'BASELINE ' if baseline else ''}exported: learn={meta['counts']['learn']} teach={meta['counts']['teach']} "
          f"office={meta['counts']['office']} books={meta['counts']['books']} collections={meta['counts']['collections']} "
          f"channels={meta['counts']['channels']}  changes={len(hist['changes'])}", flush=True)


if __name__ == "__main__":
    main()
