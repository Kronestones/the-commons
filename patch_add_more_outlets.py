"""
patch_add_more_outlets.py

Adds 15 newly verified outlets to commons/news_feed.py's NEWS_OUTLETS
list. Each URL was checked individually via web search during
development. Outlets with no confirmed official feed (NHK World,
C-SPAN, Bureau of Investigative Journalism, The Impartial Reporter)
and paywalled outlets (The Economist, Foreign Affairs, The Atlantic,
Washington Post, CNN, WSJ, USA Today, LA Times, Bloomberg Asia, NBC
News, Forbes, Financial Times, Epoch Times) were deliberately excluded.

Run once from your project root:
    python3 patch_add_more_outlets.py
"""

PATH = "commons/news_feed.py"

ANCHOR = """    {"username": "AmnestyIntl",     "rss_url": "https://www.amnesty.org/en/feed/"},  # VERIFIED
    # AP and Reuters intentionally omitted — neither offers a reliable
    # official public RSS feed anymore. Both could be added later via a
    # feed-generation service (e.g. rss.app) if you're comfortable
    # depending on a third party for that specific outlet.
]"""

NEW = """    {"username": "AmnestyIntl",     "rss_url": "https://www.amnesty.org/en/feed/"},  # VERIFIED
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
    # AP and Reuters intentionally omitted — neither offers a reliable
    # official public RSS feed anymore. NHK World Japan, C-SPAN, The
    # Bureau of Investigative Journalism, and The Impartial Reporter
    # also had no confirmed official direct feed found. Paywalled
    # outlets (The Economist, Foreign Affairs, The Atlantic, Washington
    # Post, CNN, WSJ, USA Today, LA Times, Bloomberg Asia, NBC News,
    # Forbes, Financial Times, Epoch Times) were excluded by choice —
    # this platform only auto-posts from freely-accessible sources.
]"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if '"France24"' in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write — the file may have changed since this patch was written.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting.")
        return

    content = content.replace(ANCHOR, NEW, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched commons/news_feed.py successfully — added 15 new outlets.")


if __name__ == "__main__":
    main()
