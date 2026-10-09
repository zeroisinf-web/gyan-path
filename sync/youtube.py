"""Turn the ~1,100 single YouTube links on ncert.nic.in into channels + playlists that can be embedded.

Usage:  python youtube.py
        (optional) set YOUTUBE_API_KEY to also fetch each channel's own named playlists
Writes  state/youtube_state.json:
  videos:    id -> {title, channel_url, ok}        from YouTube oEmbed (no key needed; dead/private videos -> ok False)
  channels:  url -> {name, id, uploads}             id from the channel page; uploads = 'UU…' playlist of all videos
  playlists: id -> {title, channel_url}             explicit playlist links found on NCERT + (with key) channel playlists
Only already-known videos are looked up again after 30 days, so repeat runs are cheap.
"""
import html, json, os, re, time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit, parse_qs

import requests

import paths
from catalog import Catalog

WORKERS = 4
REFRESH_DAYS = 30
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
session.headers["Accept-Language"] = "en"

VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def parse_youtube(url):
    """-> ('video', id) | ('playlist', id) | ('channel', url) | None"""
    p = urlsplit(url)
    host = (p.hostname or "").lower()
    q = parse_qs(p.query)
    if host.endswith("youtu.be"):
        vid = p.path.strip("/").split("/")[0]
        return ("video", vid) if VIDEO_ID.match(vid) else None
    if not host.endswith("youtube.com"):
        return None
    parts = [s for s in p.path.split("/") if s]
    if "list" in q and (not parts or parts[0] in ("playlist", "embed", "watch")) and not q.get("v"):
        lid = q["list"][0]
        if parts[:2] == ["embed", "videoseries"] or parts[:1] == ["playlist"] or not parts:
            return ("playlist", lid)
    if q.get("v") and VIDEO_ID.match(q["v"][0]):
        return ("video", q["v"][0])
    if len(parts) >= 2 and parts[0] in ("embed", "shorts", "live", "v") and VIDEO_ID.match(parts[1]):
        return ("video", parts[1])
    if parts and (parts[0].startswith("@") or parts[0] in ("channel", "c", "user")):
        handle = "/".join(parts[:2]) if parts[0] in ("channel", "c", "user") else parts[0]
        return ("channel", "https://www.youtube.com/" + handle)
    return None


def get(url, **kw):
    for attempt in range(3):
        try:
            return session.get(url, timeout=30, **kw)
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
    return None


def oembed(vid):
    r = get("https://www.youtube.com/oembed", params={"url": f"https://www.youtube.com/watch?v={vid}", "format": "json"})
    if r is None:
        return vid, None                                     # network trouble: keep old info
    if r.status_code != 200:
        return vid, {"ok": False, "checked": int(time.time())}
    j = r.json()
    return vid, {"ok": True, "title": j.get("title"), "channel": j.get("author_name"),
                 "channel_url": j.get("author_url"), "checked": int(time.time())}


def channel_info(url):
    r = get(url)
    if r is None or r.status_code != 200:
        return url, None
    m = (re.search(r'<meta itemprop="identifier" content="(UC[A-Za-z0-9_-]{22})"', r.text)
         or re.search(r'"externalId":"(UC[A-Za-z0-9_-]{22})"', r.text)
         or re.search(r'"channelId":"(UC[A-Za-z0-9_-]{22})"', r.text))
    name = re.search(r'<meta property="og:title" content="([^"]+)"', r.text)
    if not m:
        return url, None
    cid = m.group(1)
    return url, {"id": cid, "uploads": "UU" + cid[2:], "name": html.unescape(name.group(1)) if name else None}


def api_playlists(channel_id, key):
    """Named playlists of a channel via the YouTube Data API (only when YOUTUBE_API_KEY is set)."""
    out, token = {}, None
    while True:
        r = get("https://www.googleapis.com/youtube/v3/playlists",
                params={"part": "snippet,contentDetails", "channelId": channel_id, "maxResults": 50, "key": key,
                        **({"pageToken": token} if token else {})})
        if r is None or r.status_code != 200:
            break
        j = r.json()
        for it in j.get("items", []):
            out[it["id"]] = {"title": it["snippet"]["title"], "count": it["contentDetails"].get("itemCount")}
        token = j.get("nextPageToken")
        if not token:
            break
    return out


def main():
    cat = Catalog()
    old = json.load(open(paths.YOUTUBE_STATE, encoding="utf-8")) if os.path.exists(paths.YOUTUBE_STATE) else {}
    videos, channels, playlists = old.get("videos", {}), old.get("channels", {}), old.get("playlists", {})

    found_videos, found_channels = set(), set()
    for row in cat.rows:
        y = parse_youtube(row["URL"])
        if not y:
            continue
        kind, val = y
        if kind == "video":
            found_videos.add(val)
        elif kind == "playlist":
            playlists.setdefault(val, {"title": row["Link text"].split(" | ")[0] or None, "source": "ncert"})
        else:
            found_channels.add(val)

    cutoff = time.time() - REFRESH_DAYS * 86400
    todo = [v for v in found_videos if v not in videos or videos[v].get("checked", 0) < cutoff]
    print(f"videos on NCERT: {len(found_videos)}  to look up: {len(todo)}", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        for vid, rec in ex.map(oembed, todo):
            if rec is not None:
                videos[vid] = rec

    found_channels |= {v["channel_url"] for v in videos.values() if v.get("ok") and v.get("channel_url")}
    todo_ch = [c for c in found_channels if c not in channels]
    print(f"channels: {len(found_channels)}  to look up: {len(todo_ch)}", flush=True)
    with ThreadPoolExecutor(WORKERS) as ex:
        for url, rec in ex.map(channel_info, todo_ch):
            if rec:
                channels[url] = rec

    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        for url, ch in channels.items():
            for pid, p in api_playlists(ch["id"], key).items():
                playlists[pid] = dict(p, channel_url=url, source="api")

    state = {"updated": int(time.time()), "videos": videos, "channels": channels, "playlists": playlists}
    tmp = paths.YOUTUBE_STATE + ".tmp"
    json.dump(state, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, paths.YOUTUBE_STATE)
    ok = sum(1 for v in found_videos if videos.get(v, {}).get("ok"))
    print(f"DONE videos ok={ok} dead={sum(1 for v in found_videos if videos.get(v, {}).get('ok') is False)} "
          f"channels={len(channels)} playlists={len(playlists)}", flush=True)


if __name__ == "__main__":
    main()
