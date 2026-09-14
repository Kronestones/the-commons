"""
patch_add_batch2_outlets.py

Adds 12 newly verified outlets to commons/news_feed.py's NEWS_OUTLETS
list. Each URL was individually verified via web search/fetch during
development.

Run once from your project root:
    python3 patch_add_batch2_outlets.py
"""

PATH = "commons/news_feed.py"

ANCHOR = '''    {"username": "Axios",           "rss_url": "https://www.axios.com/feeds/feed.rss"},  # VERIFIED'''

NEW = '''    {"username": "Axios",           "rss_url": "https://www.axios.com/feeds/feed.rss"},  # VERIFIED
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
    {"username": "CSMonitor",       "rss_url": "https://rss.csmonitor.com/feeds/all"},  # VERIFIED'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if '"TheTrace"' in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting.")
        return

    content = content.replace(ANCHOR, NEW, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched commons/news_feed.py successfully — added 12 new outlets.")


if __name__ == "__main__":
    main()
