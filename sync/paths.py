"""Folder layout shared by every sync script."""
import os

SYNC = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SYNC)
STATE = os.path.join(SYNC, "state")          # crawl + link-check state (committed, makes runs incremental)
DATA = os.path.join(ROOT, "data")            # JSON the web app reads
REPORTS = os.path.join(ROOT, "reports")      # Excel / explorer analysis reports

CRAWL_STATE = os.path.join(STATE, "crawl_state.json")
LINK_STATUS = os.path.join(STATE, "link_status.json")
TEXTBOOK_STATE = os.path.join(STATE, "textbooks_state.json")
YOUTUBE_STATE = os.path.join(STATE, "youtube_state.json")
HISTORY = os.path.join(STATE, "history.json")   # first-seen / last-changed per item, feeds "What's new"

for d in (STATE, DATA, REPORTS):
    os.makedirs(d, exist_ok=True)
