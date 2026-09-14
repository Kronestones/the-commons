"""
news_feed.py — The Commons News Feed

Periodically polls RSS feeds from verified news outlets and posts new
articles as that outlet's account. Modeled on MaintenanceManager's
background-thread pattern (see commons/maintenance.py).

Every post goes through the exact same pipeline as a human post —
PostManager.create() with is_news=True — so it gets the same zero-
tolerance check and Fingerprint scan as anything else on the platform.
No bypass, no special-casing.

Deduplication: checks whether a post containing this article's URL
already exists from this outlet's account before posting again.

Codex Law 5: Transparency — every news post links back to the original
article; The Commons never reproduces full article text.
"""

import threading
from datetime import datetime
from sqlalchemy.orm import Session
from .database import SessionLocal, User, Post
from .news_fetch import safe_rss
from .posts import posts as post_manager

# ── Outlet registry ──────────────────────────────────────────────────────
# Each outlet needs a matching User account (see create_news_outlets.py)
# with username matching the "username" field below.
#
# Verified via web search + one live test (NPR) during development:
NEWS_OUTLETS = [
    {"username": "BBCNews",         "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml"},  # VERIFIED
    {"username": "NPR",             "rss_url": "https://feeds.npr.org/1001/rss.xml"},  # VERIFIED — tested live, returned 10 real entries
    {"username": "AlJazeera",       "rss_url": "https://www.aljazeera.com/xml/rss/all.xml"},  # VERIFIED
    {"username": "CBCNews",         "rss_url": "https://www.cbc.ca/cmlink/rss-topstories"},  # VERIFIED
    {"username": "MotherJones",     "rss_url": "https://www.motherjones.com/feed/"},  # VERIFIED
    {"username": "MsMagazine",      "rss_url": "https://msmagazine.com/feed/"},  # VERIFIED
    {"username": "AmnestyIntl",     "rss_url": "https://www.amnesty.org/en/feed/"},  # VERIFIED
    {"username": "France24",        "rss_url": "https://www.france24.com/en/rss"},  # VERIFIED
    {"username": "DW",              "rss_url": "https://rss.dw.com/rdf/rss-en-all"},  # VERIFIED
    {"username": "Politico",        "rss_url": "https://www.politico.com/rss/politicopicks.xml"},  # VERIFIED
    {"username": "PewResearch",     "rss_url": "https://www.pewresearch.org/feed/"},  # VERIFIED
    {"username": "TheConversation", "rss_url": "https://theconversation.com/us/articles.atom"},  # VERIFIED
    {"username": "RealNewsNetwork", "rss_url": "https://therealnews.com/feed"},  # VERIFIED
    {"username": "AlterNet",        "rss_url": "https://www.alternet.org/feeds/feed.rss"},  # VERIFIED
    {"username": "AllSides",        "rss_url": "https://www.allsides.com/rss/news"},  # VERIFIED
    {"username": "NewsNation",      "rss_url": "https://www.newsnationnow.com/feed/"},  # VERIFIED
    {"username": "Truthout",        "rss_url": "https://truthout.org/latest/feed/"},  # VERIFIED
    {"username": "HongKongFP",      "rss_url": "https://hongkongfp.com/feed/"},  # VERIFIED
    {"username": "PBSNewsHour",     "rss_url": "https://www.pbs.org/newshour/feeds/rss/nation"},  # VERIFIED
    {"username": "TheHill",         "rss_url": "https://thehill.com/feed/"},  # VERIFIED
    {"username": "AtlasNews",       "rss_url": "https://www.theatlasnews.co/feed"},  # VERIFIED
    {"username": "Axios",           "rss_url": "https://www.axios.com/feeds/feed.rss"},  # VERIFIED
    {"username": "TheTrace",        "rss_url": "https://www.thetrace.org/feed/"},  # VERIFIED
    {"username": "TheMarkup",       "rss_url": "https://themarkup.org/feeds/rss.xml"},  # VERIFIED
    {"username": "ProPublica",      "rss_url": "https://feeds.propublica.org/propublica/main"},  # VERIFIED
    {"username": "RevealNews",      "rss_url": "https://revealnews.org/feed/"},  # VERIFIED
    {"username": "Grist",           "rss_url": "https://grist.org/feed/"},  # VERIFIED
    {"username": "InsideClimateNews", "rss_url": "https://insideclimatenews.org/feed/"},  # VERIFIED
    {"username": "KFFHealthNews",   "rss_url": "https://kffhealthnews.org/feed/"},  # VERIFIED
    {"username": "The19th",         "rss_url": "https://19thnews.org/feed/"},  # VERIFIED
    {"username": "HechingerReport", "rss_url": "https://hechingerreport.org/feed/"},  # VERIFIED
    {"username": "TheGuardian",     "rss_url": "https://www.theguardian.com/world/rss"},  # VERIFIED
    {"username": "Salon",           "rss_url": "https://www.salon.com/feed/"},  # VERIFIED
    {"username": "CSMonitor",       "rss_url": "https://rss.csmonitor.com/feeds/all"},  # VERIFIED
    # AP and Reuters intentionally omitted — neither offers a reliable
    # official public RSS feed anymore. NHK World Japan, C-SPAN, The
    # Bureau of Investigative Journalism, and The Impartial Reporter
    # also had no confirmed official direct feed found. Paywalled
    # outlets (The Economist, Foreign Affairs, The Atlantic, Washington
    # Post, CNN, WSJ, USA Today, LA Times, Bloomberg Asia, NBC News,
    # Forbes, Financial Times, Epoch Times) were excluded by choice —
    # this platform only auto-posts from freely-accessible sources.
]

# How often to check feeds, in seconds. 30 minutes is a reasonable
# starting cadence.
POLL_INTERVAL_SECONDS = 30 * 60

# How many entries to look at per feed per poll.
MAX_ENTRIES_PER_POLL = 15


class NewsFeedManager:

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._last_run = None

    def start(self):
        """Start the news feed poller in background."""
        self._thread = threading.Thread(target=self._scheduler, daemon=True)
        self._thread.start()
        print("[NEWS] News feed poller started.")

    def stop(self):
        self._stop_event.set()

    def _scheduler(self):
        while not self._stop_event.is_set():
            try:
                self.run()
            except Exception as e:
                print(f"[NEWS] Error: {e}")
            self._stop_event.wait(POLL_INTERVAL_SECONDS)

    def run(self) -> dict:
        """Poll every outlet's feed once, post anything new."""
        print(f"[NEWS] Starting poll — {datetime.utcnow().isoformat()}")
        db = SessionLocal()
        results = {}

        try:
            for outlet in NEWS_OUTLETS:
                try:
                    count = self._poll_outlet(db, outlet)
                    results[outlet["username"]] = count
                except Exception as e:
                    print(f"[NEWS] Error polling {outlet['username']}: {e}")
                    results[outlet["username"]] = f"error: {e}"

            self._last_run = datetime.utcnow()
            total_posted = sum(v for v in results.values() if isinstance(v, int))
            print(f"[NEWS] Poll complete — {total_posted} new posts.")

        except Exception as e:
            print(f"[NEWS] Error during run: {e}")
            results["error"] = str(e)
        finally:
            db.close()

        return results

    def _poll_outlet(self, db: Session, outlet: dict) -> int:
        """Fetch one outlet's feed, post any new entries. Returns count posted."""
        user = db.query(User).filter(
            User.username.ilike(outlet["username"])
        ).first()

        if not user:
            print(f"[NEWS] No account found for {outlet['username']} — skipping. "
                  f"Run create_news_outlets.py to set up outlet accounts.")
            return 0

        entries = safe_rss(outlet["rss_url"])
        if not entries:
            return 0

        posted_count = 0
        for entry in entries[:MAX_ENTRIES_PER_POLL]:
            url = entry.get("link") or ""
            if not url:
                continue

            if self._already_posted(db, user.id, url):
                continue

            title = (entry.get("title") or "").strip()
            summary = self._clean_summary(entry.get("summary") or entry.get("description") or "")

            if not title:
                continue

            content = self._build_post_content(title, summary, url)

            result = post_manager.create(
                db, user, "text",
                content=content,
                is_news=True,
            )
            if result.get("ok"):
                posted_count += 1

        return posted_count

    def _already_posted(self, db: Session, author_id: int, url: str) -> bool:
        """Check if this URL has already been posted by this outlet account."""
        existing = db.query(Post).filter(
            Post.author_id == author_id,
            Post.content.like(f"%{url}%")
        ).first()
        return existing is not None

    def _clean_summary(self, raw: str) -> str:
        import re
        clean = re.sub(r"<[^>]+>", "", raw or "").strip()
        if len(clean) > 280:
            clean = clean[:277] + "..."
        return clean

    def _build_post_content(self, title: str, summary: str, url: str) -> str:
        parts = [title]
        if summary:
            parts.append(summary)
        parts.append(url)
        return "\n\n".join(parts)

    def get_status(self) -> dict:
        return {
            "last_run": self._last_run.isoformat() if self._last_run else None,
            "outlets": [o["username"] for o in NEWS_OUTLETS],
            "poll_interval_seconds": POLL_INTERVAL_SECONDS,
        }


news_feed = NewsFeedManager()
