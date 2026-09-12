"""
patch_features_youtube.py

Adds update_youtube() method to ProfileManager in commons/features.py,
matching the style of update_twitch/update_spotify.

Run once from your project root:
    python3 patch_features_youtube.py
"""

PATH = "commons/features.py"

ANCHOR = """    def update_spotify(self, db: Session, user: User, raw_input: str) -> dict:
        from commons.connections import set_spotify_connection, remove_connection
        if not raw_input.strip():
            result = remove_connection(user, "spotify")
        else:
            result = set_spotify_connection(user, raw_input)
        if result.get("ok"):
            db.commit()
        return result"""

NEW_METHOD = """

    def update_youtube(self, db: Session, user: User, raw_input: str) -> dict:
        from commons.connections import set_youtube_connection, remove_connection
        if not raw_input.strip():
            result = remove_connection(user, "youtube")
        else:
            result = set_youtube_connection(user, raw_input)
        if result.get("ok"):
            db.commit()
        return result"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "def update_youtube" in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting.")
        return

    content = content.replace(ANCHOR, ANCHOR + NEW_METHOD, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched commons/features.py successfully.")


if __name__ == "__main__":
    main()
