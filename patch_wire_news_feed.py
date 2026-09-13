"""
patch_wire_news_feed.py

Adds the news feed import and starts it in background_startup(),
alongside heartbeat/revival, so RSS polling begins automatically
when the app starts.

Run once from your project root:
    python3 patch_wire_news_feed.py
"""

PATH = "main.py"

IMPORT_ANCHOR = "from commons.maintenance    import maintenance"
IMPORT_NEW = "from commons.maintenance    import maintenance\nfrom commons.news_feed       import news_feed"

STARTUP_ANCHOR = """    def background_startup():
        try:
            revival.startup_check()
            heartbeat.start()
        except Exception as e:
            print(f"[STARTUP] Background startup warning: {e}")"""

STARTUP_NEW = """    def background_startup():
        try:
            revival.startup_check()
            heartbeat.start()
            news_feed.start()
        except Exception as e:
            print(f"[STARTUP] Background startup warning: {e}")"""


def apply_patch(content, anchor, new, label):
    count = content.count(anchor)
    if count == 0:
        print(f"ERROR: anchor for '{label}' not found. Aborting before any write.")
        return None
    if count > 1:
        print(f"ERROR: anchor for '{label}' matched {count} times (expected 1). Aborting.")
        return None
    return content.replace(anchor, new, 1)


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "from commons.news_feed" in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, IMPORT_ANCHOR, IMPORT_NEW, "import")
    if content2 is None:
        return

    content3 = apply_patch(content2, STARTUP_ANCHOR, STARTUP_NEW, "startup call")
    if content3 is None:
        return

    with open(PATH, "w") as f:
        f.write(content3)

    print("Patched main.py successfully.")


if __name__ == "__main__":
    main()
