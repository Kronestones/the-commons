"""
patch_features_bluesky_tiktok.py

Adds update_bluesky() and update_tiktok() methods to ProfileManager
in commons/features.py, matching update_youtube's exact pattern.

Run once from your project root:
    python3 patch_features_bluesky_tiktok.py
"""

PATH = "commons/features.py"

ANCHOR = '''    def update_youtube(self, db: Session, user: User, raw_input: str) -> dict:
        from commons.connections import set_youtube_connection, remove_connection
        if not raw_input.strip():
            result = remove_connection(user, "youtube")
        else:
            result = set_youtube_connection(user, raw_input)
        if result.get("ok"):
            db.commit()
        return result'''

NEW = '''    def update_youtube(self, db: Session, user: User, raw_input: str) -> dict:
        from commons.connections import set_youtube_connection, remove_connection
        if not raw_input.strip():
            result = remove_connection(user, "youtube")
        else:
            result = set_youtube_connection(user, raw_input)
        if result.get("ok"):
            db.commit()
        return result

    def update_bluesky(self, db: Session, user: User, raw_input: str) -> dict:
        from commons.connections import set_bluesky_connection, remove_connection
        if not raw_input.strip():
            result = remove_connection(user, "bluesky")
        else:
            result = set_bluesky_connection(user, raw_input)
        if result.get("ok"):
            db.commit()
        return result

    def update_tiktok(self, db: Session, user: User, raw_input: str) -> dict:
        from commons.connections import set_tiktok_connection, remove_connection
        if not raw_input.strip():
            result = remove_connection(user, "tiktok")
        else:
            result = set_tiktok_connection(user, raw_input)
        if result.get("ok"):
            db.commit()
        return result'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "def update_bluesky" in content:
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

    print("Patched commons/features.py successfully.")


if __name__ == "__main__":
    main()
