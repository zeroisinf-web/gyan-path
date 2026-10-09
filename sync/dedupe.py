"""Helpers that make each resource appear once: clean titles, language detection, duplicate merging."""
import re
from urllib.parse import urlsplit, unquote

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
URDU = re.compile(r"[؀-ۿ]")
GENERIC = re.compile(
    r"^(pdf|view|download|open|click here|here|see more|read more|more|link|file|english|hindi|urdu|e-?book|flipbook|"
    r"\(open\)|play|watch|go|details|अधिक जानें|यहाँ क्लिक करें|यहां क्लिक करें|देखें|डाउनलोड|पीडीएफ|हिंदी|हिन्दी|अंग्रेजी|"
    r"उर्दू|खोलें|लिंक|ncert|image \d+|\d+|https?://\S+)$", re.I)
LANG_WORDS = {
    "hi": r"(?:^|[\s_\-./(])(hindi|hin|hn)(?:$|[\s_\-./)])|हिंदी|हिन्दी|_h\.pdf$|hi\.pdf$",
    "en": r"(?:^|[\s_\-./(])(english|eng|en)(?:$|[\s_\-./)])|अंग्रेजी|_e\.pdf$|en\.pdf$",
    "ur": r"(?:^|[\s_\-./(])(urdu|ur)(?:$|[\s_\-./)])|उर्दू",
}
LANG_RX = {k: re.compile(v, re.I) for k, v in LANG_WORDS.items()}
STRIP_LANG = re.compile(r"(?i)[_\-\s]*(english|hindi|urdu|eng|hin|_en|_hi|_ur)(?=\.\w+$)|(?<=[a-z0-9])(en|hi|e|h)(?=\.\w+$)")


def text_parts(texts):
    """Link texts -> list of meaningful pieces (generic words like 'PDF', 'View', 'अधिक जानें' removed)."""
    out = []
    for t in texts or []:
        for piece in re.split(r"\s*\|\s*", t):
            piece = re.sub(r"\s+", " ", piece).strip(" -–:|()")
            if len(piece) >= 2 and not GENERIC.match(piece) and piece not in out:
                out.append(piece)
    return out


def from_filename(url):
    name = unquote(urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1])
    name = re.sub(r"\.\w{2,4}$", "", name)
    name = re.sub(r"[_\-]+", " ", name).strip()
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)          # CamelCase -> Camel Case
    return name[:1].upper() + name[1:] if name else ""


SHORT_LABEL = re.compile(r"(?i)^(part|unit|chapter|class|भाग|पाठ|कक्षा|set|module|volume|vol|level|grade)\b|^\S{1,14}$")


def titles(url, texts, ctx=None, page_title=""):
    """-> (title, alt_title): main title (English preferred) + the other-language title if there is one.
    A short/generic link text ('Hindi', 'भाग 2', 'Unit 3') is combined with the text around the link
    (its table row / list item), which is usually the document's real name."""
    parts = text_parts(texts)
    around = text_parts(ctx)
    long_ = [p for p in parts if not SHORT_LABEL.match(p) and len(p) > 14]
    short = [p for p in parts if p not in long_]
    pool = list(long_)
    for c in around:
        label = next((s for s in short if s.lower() not in c.lower()), "")
        pool.append(f"{c} ({label})" if label and len(c) + len(label) < 150 else c)
    pool += short
    if page_title and page_title.strip().upper() != "NCERT":
        pool.append(page_title)
    pool.append(from_filename(url))
    pool = [p.strip() for p in pool if p and p.strip()]
    en = next((p for p in pool if not DEVANAGARI.search(p) and not URDU.search(p)), "")
    hi = next((p for p in pool if DEVANAGARI.search(p)), "")
    # a filename-only English title is worse than a real Hindi one
    if en == from_filename(url) and hi:
        en, hi = hi, ""
    if not en:
        en, hi = hi or (pool[0] if pool else ""), ""
    return tidy(en)[:160], (tidy(hi) if hi != en else "")[:160]


def tidy(s):
    """'Unit 1(Real Numbers' -> 'Unit 1 (Real Numbers)'."""
    s = re.sub(r"(?<=\w)\(", " (", s or "")
    return s + ")" * max(0, s.count("(") - s.count(")"))


def languages(url, texts):
    hay = unquote(urlsplit(url).path).lower() + " " + " ".join(texts or []).lower()
    found = [k for k, rx in LANG_RX.items() if rx.search(hay)]
    return found


def lang_key(url):
    """URL with the language marker removed – English/Hindi copies of one document share this key."""
    p = urlsplit(url)
    return p.netloc + STRIP_LANG.sub("", unquote(p.path).lower())


def same_file_key(url, size):
    """Same file name + same size = the same file published at two paths."""
    if not size:
        return None
    return unquote(urlsplit(url).path).lower().rsplit("/", 1)[-1], str(size)


ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12}
CLASS_RX = re.compile(r"(?i)(?:class|grade|कक्षा|std)[\s_\-]*(xii|xi|x|ix|viii|vii|vi|v|iv|iii|ii|i|1[0-2]|[1-9])(?![a-z0-9])"
                      r"(?:\s*(?:to|-|–|से)\s*(xii|xi|x|ix|viii|vii|vi|v|iv|iii|ii|i|1[0-2]|[1-9]))?")


def classes(url, texts):
    """Class numbers mentioned in the path or link text (e.g. classVII, 'Class 6 to 8', 'कक्षा 3')."""
    hay = unquote(urlsplit(url).path) + " " + " ".join(texts or [])
    out = set()
    for m in CLASS_RX.finditer(hay):
        a = m.group(1).lower()
        a = ROMAN.get(a) or int(a)
        b = m.group(2)
        b = (ROMAN.get(b.lower()) or int(b)) if b else a
        if 1 <= a <= 12 and a <= b <= 12:
            out.update(range(a, b + 1))
    return sorted(out)
