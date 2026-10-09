"""Shared catalogue builder: crawl state -> one classified row per unique, working URL.

Used by build_report.py (Excel + explorer) and export.py (web-app JSON), so both always agree.
"""
import json, os, re, collections
from urllib.parse import urlsplit, unquote

import paths
import student_lens
from rules import excluded


def merge_key(u):
    """http/https and a trailing slash don't make a different URL."""
    p = urlsplit(u)
    return (p.netloc, p.path.rstrip("/") or "/", p.query)


# ---------- section names ----------
SECTION_NAMES = {
    "dee": "Dept. of Elementary Education (DEE)",
    "desm": "Dept. of Education in Science & Mathematics (DESM)",
    "dess": "Dept. of Education in Social Sciences (DESS)",
    "del": "Dept. of Education in Languages (DEL)",
    "dek": "Division of Educational Kits (DEK)",
    "der": "Division of Educational Research (DER)",
    "dte": "Dept. of Teacher Education (DTE)",
    "dgs": "Dept. of Gender Studies (DGS)",
    "degsn": "Dept. of Education of Groups with Special Needs (DEGSN)",
    "depfe": "Dept. of Educational Psychology & Foundations of Education (DEPFE)",
    "dcs": "Dept. of Curriculum Studies & Development (DCSD)",
    "deaa": "Dept. of Education in Arts & Aesthetics (DEAA)",
    "esd": "Educational Survey Division (ESD)",
    "pd": "Publication Division (PD)",
    "ird": "International Relations Division (IRD)",
    "pmd": "Planning & Monitoring Division (PMD)",
    "parakh": "PARAKH – National Assessment Centre",
    "ldd": "Library & Documentation Division (LDD)",
    "ncertldd": "Library & Documentation Division (LDD)",
    "cncl": "National Literacy Centre-Cell (CNCL)",
    "hc": "Hindi Cell",
    "vls": "Vigilance & Legal Section",
    "ebsb": "Ek Bharat Shreshtha Bharat (EBSB)",
    "flipbook": "Flipbooks / e-Magazines",
    "flipbook1": "Flipbooks / e-Magazines",
    "comicflipbookenglish": "Flipbooks / e-Magazines",
    "gpepub": "Flipbooks / e-Magazines",
    "statebooks": "State Textbooks",
    "uploads": "Uploads (general)",
    "images": "Images",
    "pdf": "General PDFs (/pdf)",
    "tamanna": "TAMANNA (Aptitude Test)",
    "guesthouse": "Guest House",
    "cells": "Cells",
    "qmts": "Quality Monitoring Tools (QMTs, DEE)",
    "": "Main site (root pages)",
}

TOPIC_RULES = [
    ("Recruitment & Vacancies", r"vacanc|recruit|walk.?in|interview|result|selected|shortlist|appoint|merit|admit.?card|project.?staff|deputation|empanel|rejected|eligible|waitlist|भर्ती|रिक्ति|साक्षात्कार|परिणाम|चयनित"),
    ("Tenders & Procurement", r"tender|\bbid|quotation|\beoi\b|procure|auction|\brfp\b|\bgem\b|corrigend|e-?procure|निविदा"),
    ("Pension, Insurance & Accounts", r"pension|insurance|annual.?account|\baccount|budget|salary|gpf|cghs|\bltc\b|पेंशन|बीमा|लेखा"),
    ("Fellowships & Awards", r"fellowship|award|scholar|prize|अध्येतावृत्ति|पुरस्कार|छात्रवृत्ति"),
    ("Exams, Olympiads & Assessment", r"ntse|olympiad|\bexam|assessment|\btest\b|holistic|parakh|\bnas\b|achievement|परीक्षा|मूल्यांकन|आकलन"),
    ("Admissions & Courses", r"admission|course|diploma|certificate|pgd|b\.?ed|m\.?ed|programme.?for|internship|mooc|swayam|प्रवेश|पाठ्यक्रम में प्रवेश"),
    ("Curriculum, Syllabus & Policy", r"\bncf|curricul|syllabus|guideline|policy|framework|\bnep\b|rationali[sz]|position.?paper|focus.?group|bridge|calendar|pedagog|पाठ्यचर्या|पाठ्यक्रम|दिशानिर्देश|दिशा-निर्देश|नीति"),
    ("Research, Surveys & Monitoring", r"survey|research|study|studies|evaluation|aises|data|statistic|सर्वेक्षण|शोध|अनुसंधान|अध्ययन|रिपोर्ट|प्रतिवेदन|report|qmt|monitoring"),
    ("Journals, Magazines & Newsletters", r"journal|magazine|newsletter|bulletin|sapno|udaan|firkee|\bissue|पत्रिका|जर्नल|समाचार पत्र"),
    ("Books & Publications", r"book|publication|catalogue|reader|print.?material|barkha|\bkit|manual|handbook|sourcebook|exemplar|lab.?manual|पुस्तक|किताब|प्रकाशन|कार्यपत्रक|प्राइमर|भाग \d"),
    ("Teacher Education & Training", r"teacher|training|nishtha|\bcpd|capacity|orientation|workshop.?for.?teacher|प्रशिक्षण|शिक्षक"),
    ("Events, Competitions & Days", r"competition|festival|utsav|conference|seminar|workshop|webinar|celebrat|diwas|divas|\bday\b|week|fair|exhibition|mela|foundation|yoga|quiz|poster|kala|प्रतियोगिता|उत्सव|सम्मेलन|संगोष्ठी|कार्यशाला|दिवस|समारोह|महोत्सव|पखवाड़ा"),
    ("Notices, Circulars & Orders", r"notice|circular|\border|memorandum|notification|announce|press.?release|advertis|office|सूचना|परिपत्र|आदेश|अधिसूचना|विज्ञापन"),
    ("e-Content & Digital Learning", r"e-?content|digital|e-?pathshala|diksha|ciet|video|audio|podcast|youtube|app\b|online|ict|virtual|flipbook|epub|ई-सामग्री|डिजिटल|वीडियो"),
    ("Inclusive & Special Needs", r"cwsn|disab|special.?need|inclusive|sign.?language|braille|accessib|divyang|gender|girl|दिव्यांग|समावेशी"),
    ("Vocational Education", r"vocation|psscive|skill|व्यावसायिक"),
    ("Guidance, Counselling & Wellbeing", r"counsel|guidance|career|mental|wellbeing|well-being|health|tamanna|manodarpan|परामर्श|मार्गदर्शन"),
    ("About NCERT & Administration", r"about|minutes|meeting|management|कार्यवृत्त|बैठक|functionar|organo|\brti\b|contact|director|council|committee|administ|annual.?report|charter|sitemap|disclaimer|privacy|hindi.?cell|vigilance|grievance|faculty|staff|faq|help|feedback|screen.?reader|history|vision|mission|department|division|cell|guest.?house|library|campus|के बारे में|संपर्क|सदस्य|स्टाफ|प्रभाग|विभाग|प्रकोष्ठ|पुस्तकालय"),
]
PATH_RULES = [
    ("Photo Gallery & News", r"gallery|news-content|^/images/|/photos?/"),
    ("Library & Documentation Services", r"pressclips|currentcontents|^/ldd/|^/ncertldd/"),
    ("Research, Surveys & Monitoring", r"^/qmts/|/nas/"),
    ("Learning Resources (primers, worksheets, modules)", r"primer|worksheet|margdarshika|/chandrayan/|/resources/|/module/"),
    ("Books & Publications", r"^/statebooks/|/publication/"),
]
PATH_RX = [(n, re.compile(r, re.I)) for n, r in PATH_RULES]
TOPIC_RX = [(n, re.compile(r, re.I)) for n, r in TOPIC_RULES]

DOC_EXT = {"pdf": "PDF", "doc": "Word", "docx": "Word", "xls": "Excel", "xlsx": "Excel", "csv": "Excel",
           "ppt": "PowerPoint", "pptx": "PowerPoint", "pps": "PowerPoint", "ppsx": "PowerPoint",
           "zip": "Archive (zip/rar)", "rar": "Archive (zip/rar)", "7z": "Archive (zip/rar)",
           "txt": "Text", "rtf": "Word", "odt": "Word", "epub": "e-Book (epub)"}
IMG_EXT = {"jpg", "jpeg", "png", "gif", "bmp", "svg", "webp", "ico"}
AV_EXT = {"mp4", "mp3", "wav", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4a", "ogg", "swf"}

SOCIAL = re.compile(r"(youtube\.com|youtu\.be|facebook\.com|twitter\.com|x\.com|instagram\.com|linkedin\.com|whatsapp|t\.me|koo\.in|threads\.net)$")
NCERT_FAMILY = re.compile(r"(ncert\.gov\.in|ncert\.org\.in|ncerttech\.in|ciet\.nic\.in|epathshala\.nic\.in|nerie\.nic\.in|riea|rieb|riem|riemysore|psscive|ncertx\.in|ncertrec|diksha\.gov\.in|aises\.nic\.in|ictcurriculum)")
GOV = re.compile(r"(\.gov\.in|\.nic\.in|\.gov|mygov\.in|g20\.in)$")


def classify(u, r, crawled):
    p = urlsplit(u)
    host = p.hostname or ""
    path = unquote(p.path)
    ext = path.rsplit(".", 1)[-1].lower() if "." in path.rsplit("/", 1)[-1] else ""
    segs = [s for s in path.split("/") if s]

    # ---- category (what kind of thing) ----
    if host != "ncert.nic.in":
        if SOCIAL.search(host):
            cat = "External – Social media & YouTube"
        elif NCERT_FAMILY.search(host):
            cat = "External – NCERT portals & institutes"
        elif GOV.search(host) or re.match(r"^\d+\.\d+\.\d+\.\d+$", host):
            cat = "External – Government sites"
        else:
            cat = "External – Other websites"
        kind = "External link"
    elif ext in DOC_EXT:
        cat, kind = "Documents (PDF / Word / Excel / PPT / ZIP)", DOC_EXT[ext]
    elif ext in IMG_EXT:
        cat, kind = "Images", "Image"
    elif ext in AV_EXT:
        cat, kind = "Audio / Video", "Audio/Video"
    elif segs and (segs[0].lower().startswith("flipbook") or segs[0].lower() in ("comicflipbookenglish", "gpepub")):
        cat, kind = "Flipbooks / e-Magazines", "Flipbook"
    else:
        ct = (r.get("ctype") or "")
        if ct and "html" not in ct:
            cat, kind = "Documents (PDF / Word / Excel / PPT / ZIP)", ct
        else:
            cat, kind = "Web pages (ncert.nic.in)", "Web page"

    # ---- section (where on the site / which site) ----
    sub = ""
    if host != "ncert.nic.in":
        section = host
        sub = "/".join(segs[:-1][:2]) if len(segs) > 1 else ""
    else:
        key = ""
        if len(segs) > 1 or (segs and ext == "" and "." not in segs[0]):
            key = segs[0].lower()
            if key in ("division", "departments", "sections") and len(segs) > 2:
                key = segs[1].lower()
        section = SECTION_NAMES.get(key) or f"/{key} folder"
        skip = 2 if segs and segs[0].lower() in ("division", "departments", "sections", "cells") and len(segs) > 2 else 1
        if key == "pdf" and len(segs) > 2:
            section = f"General PDFs (/pdf/{segs[1]})"
            skip = 2
        folders = segs[skip:] if p.path.endswith("/") else segs[skip:-1]
        sub = "/".join(folders[:3]) if key else ""

    # ---- topic (what it is about) ----
    hay = " ".join([path.replace("_", " ").replace("-", " "), " ".join(r.get("texts") or []), r.get("title") or ""])
    topic = "Other / General"
    for name, rx in PATH_RX if host == "ncert.nic.in" else []:
        if rx.search(path):
            topic = name
            break
    if topic != "Other / General":
        pass
    elif host == "ncert.nic.in" or cat.endswith("Other websites"):
        for name, rx in TOPIC_RX:
            if rx.search(hay):
                topic = name
                break
    else:
        topic = "Link to other site"

    langs = set(r.get("langs") or [])
    if r.get("has_hindi_page"):
        langs.add("hi")
    if u in crawled or langs:
        langs.add("en")
    lang = "English + Hindi" if {"en", "hi"} <= langs else ("Hindi" if "hi" in langs else "")

    status = r.get("status")
    if host == "ncert.nic.in" and u not in crawled and kind == "Web page":
        status = "not fetched"
    return {
        "Category": cat, "Section": section, "Sub-section": sub, "Topic": topic, "Type": kind,
        "URL": u, "Link text": " | ".join(r.get("texts") or []), "Page title": r.get("title") or "",
        "Linked from (pages)": r.get("found_on_count", 0),
        "Example pages linking here": "\n".join((r.get("found_on") or [])[:3]),
        "Language": lang, "Status": "" if status in (None, 200) else str(status),
        "Redirects to": r.get("final_url") or "",
    }


CAT_ORDER = ["Web pages (ncert.nic.in)", "Documents (PDF / Word / Excel / PPT / ZIP)", "Flipbooks / e-Magazines",
             "Images", "Audio / Video", "External – NCERT portals & institutes", "External – Government sites",
             "External – Social media & YouTube", "External – Other websites"]


def broken(row, link_status):
    """True when the URL definitely does not work. Outside sites that merely block robots (403/429) or are slow are kept."""
    u = row["URL"]
    own = urlsplit(u).hostname == "ncert.nic.in"
    if row["Status"] and row["Status"] != "not fetched":       # crawled page that returned an error
        return True
    s = (link_status.get(u) or {}).get("status")
    if s is None:
        return False
    if isinstance(s, int):
        if s in (404, 410) or (own and s >= 400):
            return True
        row["Redirects to"] = row["Redirects to"] or ((link_status[u].get("final") or "") if s < 400 else "")
        return False
    return own or s == "dns/connection error"                  # no response at all


class Catalog:
    """rows: working URLs (classified + student lens); removed: broken ones; urls: merged crawl records."""

    def __init__(self, crawl_state=paths.CRAWL_STATE, link_status=paths.LINK_STATUS):
        st = json.load(open(crawl_state, encoding="utf-8"))
        self.crawled = set(st["done"])
        self.link_status = json.load(open(link_status, encoding="utf-8")) if os.path.exists(link_status) else {}

        # merge duplicates; prefer https and the crawled spelling
        merged = {}
        for u, r in sorted(st["urls"].items(), key=lambda kv: (kv[0] not in self.crawled, not kv[0].startswith("https"), kv[0])):
            k = merge_key(u)
            if k not in merged:
                merged[k] = dict(r, url=u, found_on=list(r.get("found_on") or []))
            else:
                m = merged[k]
                seen = set(m["found_on"])
                m["found_on"] += [x for x in r.get("found_on") or [] if x not in seen]
                m["texts"] = (m.get("texts") or []) + [t for t in r.get("texts") or [] if t not in (m.get("texts") or [])][:8]
                m["langs"] = sorted(set(m.get("langs") or []) | set(r.get("langs") or []))
                m["ctx"] = (m.get("ctx") or []) + [c for c in r.get("ctx") or [] if c not in (m.get("ctx") or [])][:3]
        self.urls = {r["url"]: r for r in merged.values()}
        # count only linking pages that are themselves part of the inventory (not excluded book pages)
        for r in self.urls.values():
            r["found_on"] = sorted({x for x in r["found_on"] if not excluded(x)})
            r["found_on_count"] = len(r["found_on"])

        rows, self.n_excluded = [], 0
        for u, r in self.urls.items():
            if excluded(u):
                self.n_excluded += 1
                continue
            rows.append(classify(u, r, self.crawled))
        self.removed = [r for r in rows if broken(r, self.link_status)]
        rows = [r for r in rows if not broken(r, self.link_status)]

        # each folder's own index page title names sections we have no name for
        self.section_titles = {}
        for row in rows:
            p = urlsplit(row["URL"])
            if (row["Type"] == "Web page" and row["Page title"] and row["Page title"].strip().upper() != "NCERT"
                    and row["Section"].endswith(" folder") and re.search(r"/(index\.php)?$", p.path)):
                self.section_titles.setdefault(row["Section"], row["Page title"])

        rows.sort(key=lambda x: (CAT_ORDER.index(x["Category"]) if x["Category"] in CAT_ORDER else 99,
                                 x["Section"].lower(), x["Sub-section"].lower(), x["Topic"], x["URL"].lower()))
        student_lens.assign(rows, self.urls)
        self.rows = rows
