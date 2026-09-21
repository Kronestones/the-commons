"""
patch_add_batch3_outlets.py

Adds 5 more verified outlets to commons/news_feed.py's NEWS_OUTLETS
list, bringing the total to 39.

Run once from your project root:
    python3 patch_add_batch3_outlets.py
"""

PATH = "commons/news_feed.py"

ANCHOR = '''    {"username": "CSMonitor",       "rss_url": "https://rss.csmonitor.com/feeds/all"},  # VERIFIED'''

NEW = '''    {"username": "CSMonitor",       "rss_url": "https://rss.csmonitor.com/feeds/all"},  # VERIFIED
    {"username": "DemocracyNow",     "rss_url": "https://www.democracynow.org/democracynow.rss"},  # VERIFIED
    {"username": "ScienceNews",      "rss_url": "https://www.sciencenews.org/feed"},  # VERIFIED
    {"username": "NonprofitQuarterly", "rss_url": "https://nonprofitquarterly.org/feed/"},  # VERIFIED
    {"username": "Bellingcat",       "rss_url": "https://www.bellingcat.com/feed/"},  # VERIFIED
    {"username": "SpotlightPA",      "rss_url": "https://www.spotlightpa.org/feeds/full.xml"},  # VERIFIED'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if '"DemocracyNow"' in content:
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

    print("Patched commons/news_feed.py successfully — added 5 new outlets.")


if __name__ == "__main__":
    main()
