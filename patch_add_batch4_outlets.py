"""
patch_add_batch4_outlets.py

Adds 6 more verified outlets to commons/news_feed.py's NEWS_OUTLETS
list, bringing the total to 45.

Run once from your project root:
    python3 patch_add_batch4_outlets.py
"""

PATH = "commons/news_feed.py"

ANCHOR = '''    {"username": "SpotlightPA",      "rss_url": "https://www.spotlightpa.org/feeds/full.xml"},  # VERIFIED'''

NEW = '''    {"username": "SpotlightPA",      "rss_url": "https://www.spotlightpa.org/feeds/full.xml"},  # VERIFIED
    {"username": "CalMatters",       "rss_url": "https://calmatters.org/feed/"},  # VERIFIED
    {"username": "WyoFile",          "rss_url": "https://wyofile.com/feed/"},  # VERIFIED
    {"username": "BlockClubChicago", "rss_url": "https://blockclubchicago.org/feed/"},  # VERIFIED
    {"username": "LAist",            "rss_url": "https://laist.com/rss-feed"},  # VERIFIED
    {"username": "MinnPost",         "rss_url": "https://www.minnpost.com/feed/"},  # VERIFIED
    {"username": "HighCountryNews",  "rss_url": "https://www.hcn.org/feed/"},  # VERIFIED'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if '"CalMatters"' in content:
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

    print("Patched commons/news_feed.py successfully — added 6 new outlets.")


if __name__ == "__main__":
    main()
