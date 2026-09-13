"""
news_fetch.py — The Commons safe RSS fetcher

Every outbound RSS request goes through here. Never raises — returns
[] on any failure, so a broken feed never crashes the news poller.
Handles: timeouts, retries, rate-limit backoff, a real user-agent.

Adapted from a safe-fetch pattern originally built for a different
Commons-adjacent project; reused here because a retry/backoff/never-
crash HTTP wrapper is the same problem regardless of what's being
fetched.
"""

import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

HEADERS = {
    "User-Agent": (
        "TheCommons/1.0 (community news aggregator; "
        "contact: sentinel.commons@gmail.com)"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# Retry on 429, 500, 502, 503, 504
_RETRY = Retry(
    total=3,
    backoff_factor=2,          # 2s, 4s, 8s
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    raise_on_status=False,
)

_SESSION = requests.Session()
_SESSION.mount("https://", HTTPAdapter(max_retries=_RETRY))
_SESSION.mount("http://", HTTPAdapter(max_retries=_RETRY))


def safe_get(url: str, timeout: int = 15) -> requests.Response | None:
    """
    GET url with retry/backoff. Returns Response or None.
    Caller checks .ok and parses .content themselves.
    """
    try:
        resp = _SESSION.get(url, headers=HEADERS, timeout=timeout)
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 10))
            print(f"[news_fetch] 429 from {url[:60]} — waiting {retry_after}s")
            time.sleep(retry_after)
            resp = _SESSION.get(url, headers=HEADERS, timeout=timeout)
        return resp
    except Exception as e:
        print(f"[news_fetch] FAIL {url[:80]}: {e}")
        return None


def safe_rss(url: str, timeout: int = 15) -> list:
    """
    Fetch and parse an RSS/Atom feed.
    Returns list of feedparser entries, or [] on any failure.
    Never raises — a broken or unreachable feed just yields no entries.
    """
    try:
        import feedparser
        resp = safe_get(url, timeout=timeout)
        if resp is None or not resp.ok:
            return []
        feed = feedparser.parse(resp.content)
        return feed.entries if hasattr(feed, "entries") else []
    except Exception as e:
        print(f"[news_fetch] RSS error {url[:80]}: {e}")
        return []
