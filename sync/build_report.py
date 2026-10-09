"""Write the analysis reports (reports/NCERT_URLs.xlsx, NCERT_URL_Explorer.html, removed-URL CSV) from the shared catalogue."""
import csv, json, os, collections

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

import paths
import student_lens
from catalog import Catalog, CAT_ORDER

HERE = paths.SYNC
OUT = paths.REPORTS
cat = Catalog()
rows, removed, n_excl, CRAWLED = cat.rows, cat.removed, cat.n_excluded, cat.crawled
idx_title, LINK_STATUS = cat.section_titles, cat.link_status

with open(os.path.join(OUT, "NCERT_removed_broken_urls.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["URL", "Error", "Link text", "Example page linking here"])
    for r in removed:
        err = r["Status"] or str((LINK_STATUS.get(r["URL"]) or {}).get("status"))
        w.writerow([r["URL"], err, r["Link text"], r["Example pages linking here"].split("\n")[0]])

LENS = ["Reaches learner", "Eventual product for learner"]
COLS = ["Category", "Section", "Sub-section", "Topic"] + LENS + ["Type", "URL", "What it is / used for", "Link text",
        "Page title", "Linked from (pages)", "Example pages linking here", "Language", "Status", "Redirects to", "Lens basis"]
LENS_COLS = LENS + ["URL", "What it is / used for", "Link text", "Section", "Sub-section", "Type", "Linked from (pages)", "Lens basis"]
WIDTH = {"Category": 26, "Section": 34, "Sub-section": 24, "Topic": 26, "Type": 12, "URL": 70, "Link text": 45, "Page title": 35,
         "Linked from (pages)": 11, "Example pages linking here": 50, "Language": 13, "Status": 10, "Redirects to": 40,
         "Reaches learner": 30, "Eventual product for learner": 24, "What it is / used for": 60, "Lens basis": 18}

# ---------- Excel ----------
wb = Workbook()
HFILL = PatternFill("solid", fgColor="1F4E78")
HFONT = Font(color="FFFFFF", bold=True)


def sheet(ws, data, cols=COLS):
    ws.append(cols)
    for c in ws[1]:
        c.fill, c.font = HFILL, HFONT
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for d in data:
        ws.append([d[c] for c in cols])
        cell = ws.cell(ws.max_row, cols.index("URL") + 1)
        cell.hyperlink = d["URL"]
        cell.font = Font(color="0563C1", underline="single")
    for i, c in enumerate(cols, 1):
        ws.column_dimensions[get_column_letter(i)].width = WIDTH.get(c, 15)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


ws = wb.active
ws.title = "Summary"
cat_count = collections.Counter(r["Category"] for r in rows)
sec_count = collections.Counter((r["Category"], r["Section"]) for r in rows)
topic_count = collections.Counter(r["Topic"] for r in rows if not r["Category"].startswith("External"))
ws.append(["NCERT website (ncert.nic.in) – inventory of unique URLs"]); ws["A1"].font = Font(bold=True, size=14)
ws.append([f"Pages crawled: {len(CRAWLED)} (English + ?ln=hi Hindi version of each)   |   Unique URLs listed: {len(rows)}"])
ws.append([f"Broken URLs removed: {len(removed)} (page not found / server error / site no longer exists). "
           "They are listed separately in NCERT_removed_broken_urls.csv. Outside websites that only block automated checks are kept."])
ws.append([f"Excluded on request: {n_excl} individual book URLs – textbook chapter PDFs (/textbook/pdf/*), per-book views "
           "(textbook.php?<book>, vocational.php?<book>, R3_learning_Resources.php?<book>), inner pages of storybook e-books "
           "and flipbooks. The selector pages (e.g. https://ncert.nic.in/textbook.php) and each e-book/flipbook's main URL are kept."])
ws.append(["Duplicates removed: http/https, www., #anchors, ?ln=en/?ln=hi language switches and query-parameter order "
           "are treated as the same URL. 'Linked from (pages)' shows how many different pages link to each URL."])
ws.append([])
ws.append(["Category", "Unique URLs"])
for c in ws[ws.max_row]: c.font = Font(bold=True)
for c in CAT_ORDER:
    if cat_count.get(c): ws.append([c, cat_count[c]])
ws.append([])
ws.append(["Category", "Section", "Unique URLs"])
for c in ws[ws.max_row]: c.font = Font(bold=True)
for (c, s), n in sorted(sec_count.items(), key=lambda x: (CAT_ORDER.index(x[0][0]) if x[0][0] in CAT_ORDER else 99, -x[1])):
    ws.append([c, s + (f"  –  {idx_title[s]}" if s in idx_title else ""), n])
ws.append([])
ws.append(["Topic (ncert.nic.in URLs only)", "Unique URLs"])
for c in ws[ws.max_row]: c.font = Font(bold=True)
for t, n in topic_count.most_common():
    ws.append([t, n])
ws.column_dimensions["A"].width = 48; ws.column_dimensions["B"].width = 70; ws.column_dimensions["C"].width = 14

# ---------- Student lens summary ----------
R = student_lens.ROLE
role_of = {v: k for k, v in R.items()}
wl = wb.create_sheet("Student Lens")
B = Font(bold=True)
wl.append(["Student lens – does this URL deliver a product to the learner?"]); wl["A1"].font = Font(bold=True, size=14)
wl.append(["The whole system exists to deliver products to the learner: knowledge, skill, better thinking, opportunity/money "
           "and wellbeing. Where or how it is delivered (school, home, bus, website, seminar) matters less than whether it "
           "reaches the learner. Every URL is placed on a ladder from 'the learner uses it directly' (1) to 'the organisation "
           "maintaining itself' (6). Rows marked 'guessed' in Lens basis are rule-of-thumb and worth a quick check."])
wl["A2"].alignment = Alignment(wrap_text=True, vertical="top"); wl.merge_cells("A2:H2"); wl.row_dimensions[2].height = 75
wl.append([])
wl.append(["Reaches learner", "What it means", "URLs", "% of all", "Web pages", "Documents & media", "External links"])
for c in wl[wl.max_row]: c.font = B
tot = len(rows)
for k, label in R.items():
    sub = [r for r in rows if r["Reaches learner"] == label]
    wl.append([label, student_lens.ROLE_EXPLAIN[k], len(sub), round(100 * len(sub) / tot, 1),
               sum(r["Category"] == "Web pages (ncert.nic.in)" for r in sub),
               sum(not r["Category"].startswith(("Web pages", "External")) for r in sub),
               sum(r["Category"].startswith("External") for r in sub)])
    wl.cell(wl.max_row, 2).alignment = Alignment(wrap_text=True, vertical="top")
wl.append([])
wl.append(["Eventual product for learner"] + [R[k] for k in "DGTS"] + ["Total"])
for c in wl[wl.max_row]: c.font = B; c.alignment = Alignment(wrap_text=True)
prods = student_lens.PRODUCTS + [student_lens.MIXED]
for pr in prods:
    cnt = [sum(r["Eventual product for learner"] == pr and r["Reaches learner"] == R[k] for r in rows) for k in "DGTS"]
    wl.append([pr] + cnt + [sum(cnt)])
wl.append([])
wl.append(["Section of ncert.nic.in (where the work sits)"] + [R[k] for k in "DGTSPO"] + ["Total", "% reaching learner directly (1+2)"])
for c in wl[wl.max_row]: c.font = B; c.alignment = Alignment(wrap_text=True)
secs = collections.defaultdict(collections.Counter)
for r in rows:
    if not r["Category"].startswith("External"):
        secs[r["Section"]][role_of[r["Reaches learner"]]] += 1
for sname, c in sorted(secs.items(), key=lambda x: -sum(x[1].values())):
    t = sum(c.values())
    wl.append([sname] + [c[k] for k in "DGTSPO"] + [t, round(100 * (c["D"] + c["G"]) / t)])
wl.append([])
wl.append([f"Lens basis: rule / named page = {sum(r['Lens basis'] == 'rule' for r in rows)},  inherited from the page that "
           f"lists it = {sum(r['Lens basis'] == 'inherited from linking page' for r in rows)},  inherited from a mixed shelf "
           f"(worth checking) = {sum('mixed shelf' in r['Lens basis'] for r in rows)},  guessed from topic = "
           f"{sum(r['Lens basis'].startswith('guessed') for r in rows)}.  Filter the 'Lens basis' column to review."])
wl.column_dimensions["A"].width = 52; wl.column_dimensions["B"].width = 70
for col in "CDEFGHIJ":
    wl.column_dimensions[col].width = 16
wl.freeze_panes = "A4"

# ---------- Glossary ----------
wg = wb.create_sheet("Glossary")
wg.append(["Term", "What it means"])
for c in wg[1]: c.fill, c.font = HFILL, HFONT
for t, d in student_lens.GLOSSARY:
    wg.append([t, d])
    wg.cell(wg.max_row, 2).alignment = Alignment(wrap_text=True, vertical="top")
wg.column_dimensions["A"].width = 26; wg.column_dimensions["B"].width = 110
wg.freeze_panes = "A2"

SHEETS = [
    ("1-2 Direct to Learner", lambda r: r["Reaches learner"][0] in "12"),
    ("3-7 Not Direct (explained)", lambda r: r["Reaches learner"][0] in "34567"),
    ("Web Pages", lambda r: r["Category"] == "Web pages (ncert.nic.in)"),
    ("Documents", lambda r: r["Category"].startswith("Documents")),
    ("Flipbooks & Media", lambda r: r["Category"] in ("Flipbooks / e-Magazines", "Images", "Audio / Video")),
    ("External Sites", lambda r: r["Category"].startswith("External")),
    ("Most Repeated", None),
    ("Redirected", lambda r: r["Redirects to"]),
    ("All URLs", lambda r: True),
]
for name, pred in SHEETS:
    w = wb.create_sheet(name)
    if name == "Most Repeated":
        data = sorted((r for r in rows if r["Linked from (pages)"] >= 5), key=lambda r: -r["Linked from (pages)"])
    else:
        data = [r for r in rows if pred(r)]
    if name[0].isdigit():
        data = sorted(data, key=lambda r: (r["Reaches learner"], r["Eventual product for learner"], r["Section"], r["URL"]))
        sheet(w, data, LENS_COLS)
    else:
        sheet(w, data)
wb.move_sheet("Glossary", offset=len(wb.sheetnames) - 1 - wb.sheetnames.index("Glossary"))
xlsx = os.path.join(OUT, "NCERT_URLs.xlsx")
wb.save(xlsx)

# ---------- HTML explorer ----------
data = [[r["Category"], r["Section"], r["Topic"], r["Type"], r["URL"], r["Link text"][:200],
         r["Page title"][:150], r["Linked from (pages)"], r["Language"], r["Status"], r["Sub-section"],
         r["Reaches learner"], r["Eventual product for learner"], r["What it is / used for"]] for r in rows]
tpl = open(os.path.join(HERE, "explorer_template.html"), encoding="utf-8").read()
page = (tpl.replace("/*DATA*/[]", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
           .replace("/*SECTION_TITLES*/{}", json.dumps(idx_title, ensure_ascii=False))
           .replace("/*ROLE_EXPLAIN*/{}", json.dumps({student_lens.ROLE[k]: v for k, v in student_lens.ROLE_EXPLAIN.items()}, ensure_ascii=False))
           .replace("{{EXCLUDED}}", str(n_excl)).replace("{{REMOVED}}", str(len(removed))).replace("{{CRAWLED}}", str(len(CRAWLED))))
htm = os.path.join(OUT, "NCERT_URL_Explorer.html")
open(htm, "w", encoding="utf-8").write(page)
print(f"rows={len(rows)} excluded={n_excl} crawled={len(CRAWLED)} removed_broken={len(removed)}")
for c in CAT_ORDER: print(f"  {cat_count.get(c,0):6d}  {c}")
for k, v in collections.Counter(r["Reaches learner"] for r in rows).most_common(): print(f"  {v:6d}  {k}")
print("  guessed:", sum(r["Lens basis"].startswith("guessed") for r in rows))
print("wrote", xlsx, "and", htm)
