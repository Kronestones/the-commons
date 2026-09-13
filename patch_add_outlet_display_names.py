"""
patch_add_outlet_display_names.py

Adds display names for the 15 newly added outlets to
create_news_outlets.py's DISPLAY_NAMES dict.

Run once from your project root, then re-run
create_news_outlets.py to create the new accounts:
    python3 patch_add_outlet_display_names.py
    python3 create_news_outlets.py
"""

PATH = "create_news_outlets.py"

ANCHOR = '''DISPLAY_NAMES = {
    "BBCNews":     "BBC News",
    "NPR":         "NPR",
    "AlJazeera":   "Al Jazeera",
    "CBCNews":     "CBC News",
    "MotherJones": "Mother Jones",
    "MsMagazine":  "Ms. Magazine",
    "AmnestyIntl": "Amnesty International",
}'''

NEW = '''DISPLAY_NAMES = {
    "BBCNews":     "BBC News",
    "NPR":         "NPR",
    "AlJazeera":   "Al Jazeera",
    "CBCNews":     "CBC News",
    "MotherJones": "Mother Jones",
    "MsMagazine":  "Ms. Magazine",
    "AmnestyIntl": "Amnesty International",
    "France24":        "France 24",
    "DW":              "DW",
    "Politico":        "Politico",
    "PewResearch":     "Pew Research Center",
    "TheConversation": "The Conversation",
    "RealNewsNetwork": "The Real News Network",
    "AlterNet":        "AlterNet",
    "AllSides":        "AllSides",
    "NewsNation":      "NewsNation",
    "Truthout":        "Truthout",
    "HongKongFP":      "Hong Kong Free Press",
    "PBSNewsHour":     "PBS NewsHour",
    "TheHill":         "The Hill",
    "AtlasNews":       "Atlas News",
    "Axios":           "Axios",
}'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if '"France24":' in content:
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

    print("Patched create_news_outlets.py successfully.")


if __name__ == "__main__":
    main()
