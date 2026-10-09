# ज्ञान पथ · Gyan Path

An **unofficial, learner-first index of everything on [ncert.nic.in](https://ncert.nic.in/)** – a small web app
(installable on phones) that:

- puts **what the learner actually uses** first: textbooks chapter-wise, videos, practice, reading, interactives,
  skills, wellbeing & career, opportunities, adult literacy;
- keeps **teachers' material** and the **office side** (policy, research, notices, jobs, tenders, RTI) separate;
- shows **each resource once**: duplicate links, copies at two paths and English/Hindi versions are merged;
- turns ~1,100 single YouTube links into **11 channels and 25 playable collections**;
- **works offline** for browsing and search; you can also add downloaded NCERT PDFs and read them offline;
- **collects nothing** – no accounts, cookies, analytics; YouTube loads only when you press play;
- **follows NCERT automatically**: a GitHub Action reads the site every 6 hours, drops broken links and
  records what was added, changed or removed (the app's *What's new*).

It never re-hosts NCERT's files – every link opens ncert.nic.in or YouTube. All content © NCERT.

## How it is put together

```
sync/                 Python – turns ncert.nic.in into the app's data
  crawl.py            reads every page (English + Hindi), records every link and the text around it
  check_links.py      HEAD-checks files and outside links; Last-Modified/size detect updated files
  textbooks.py        reads textbook.php's book menu, verifies each chapter PDF
  youtube.py          video links -> channels (oEmbed, no key) [+ named playlists with YOUTUBE_API_KEY]
  rules.py            which URLs are left out (per-book pages, e-book inner pages)
  catalog.py          one classified row per working URL (shared by the report and the app)
  student_lens.py     how directly each URL reaches the learner + a plain note on what it is for
  dedupe.py           titles, languages, duplicate merging, class detection
  export.py           writes data/*.json and the What's-new history; refuses to publish if the site shrank >30%
  build_report.py     reports/NCERT_URLs.xlsx + NCERT_URL_Explorer.html (the analysis workbook)
  build_site.py       web/ + data/ -> site/ (what GitHub Pages serves)
data/                 the catalogue the app reads (committed by the sync job)
web/                  the app: plain JavaScript, no framework, Hindi + English
.github/workflows/sync.yml   the 6-hourly sync + deploy
```

## Run it on your computer

```bash
cd sync
pip install -r requirements.txt
python crawl.py --fresh      # ~3 min
python check_links.py        # first time ~30 min (all files), then only new + 1/7 of the rest
python textbooks.py          # first time ~45 min (verifies ~20,000 chapter files), then only when the menu changes
python youtube.py
python export.py
python build_site.py
python -m http.server 8766 --directory ../site      # open http://localhost:8766
```

## Put it online (free, GitHub)

1. Create a new GitHub repository and push this folder to it.
2. Repository **Settings → Pages → Source: GitHub Actions**.
3. **Actions → Sync with NCERT → Run workflow** once. After that it runs by itself every 6 hours.
4. Optional: add a free YouTube Data API key as the secret `YOUTUBE_API_KEY` to also show each channel's named playlists.

If a sync fails (for example NCERT redesigns its site), the app keeps showing the last good data and the
workflow opens a GitHub issue labelled `sync-failure`.

## Known limits

- PDFs and videos need internet (NCERT's server does not allow other sites to store its files); downloaded PDFs can
  be added under **My shelf** to read offline.
- New NCERT material appears within about 6 hours. Videos inside a channel/collection player are always current.
- Some NCERT links only say "PDF" or "View"; titles are built from the surrounding table row/list, which is
  usually – not always – the document's real name.
