"""
patch_add_batch4_display_names.py

Adds display names for the 6 newly added outlets to
create_news_outlets.py's DISPLAY_NAMES dict.

Run once from your project root, then re-run
create_news_outlets.py to create the new accounts:
    python3 patch_add_batch4_display_names.py
    python3 create_news_outlets.py
"""

PATH = "create_news_outlets.py"

ANCHOR = '''    "SpotlightPA":        "Spotlight PA",
}'''

NEW = '''    "SpotlightPA":        "Spotlight PA",
    "CalMatters":         "CalMatters",
    "WyoFile":            "WyoFile",
    "BlockClubChicago":   "Block Club Chicago",
    "LAist":              "LAist",
    "MinnPost":           "MinnPost",
    "HighCountryNews":    "High Country News",
}'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if '"CalMatters":' in content:
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

    print("Patched create_news_outlets.py successfully.")


if __name__ == "__main__":
    main()
