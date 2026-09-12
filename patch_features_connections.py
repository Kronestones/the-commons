"""
patch_features_connections.py

Adds update_twitch() and update_spotify() methods to ProfileManager
in commons/features.py, matching the style of update_bio/update_display_name.

Run once from your project root:
    python3 patch_features_connections.py
"""

PATH = "commons/features.py"

ANCHOR = """    def update_display_name(self, db: Session, user: User,
                             display_name: str) -> dict:
        if len(display_name) > 100:
            return {"ok": False, "error": "Display name must be 100 characters or fewer."}
        user.display_name = display_name
        db.commit()
        return {"ok": True}"""

NEW_METHODS = """

    def update_twitch(self, db: Session, user: User, raw_input: str) -> dict:
        from commons.connections import set_twitch_connection, remove_connection
        if not raw_input.strip():
            result = remove_connection(user, "twitch")
        else:
            result = set_twitch_connection(user, raw_input)
        if result.get("ok"):
            db.commit()
        return result

    def update_spotify(self, db: Session, user: User, raw_input: str) -> dict:
        from commons.connections import set_spotify_connection, remove_connection
        if not raw_input.strip():
            result = remove_connection(user, "spotify")
        else:
            result = set_spotify_connection(user, raw_input)
        if result.get("ok"):
            db.commit()
        return result"""

def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "def update_twitch" in content:
        print("Already patched — no changes made.")
        return

    if ANCHOR not in content:
        print("ERROR: anchor block not found. File may have changed — aborting, nothing written.")
        return

    content = content.replace(ANCHOR, ANCHOR + NEW_METHODS, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched commons/features.py successfully.")

if __name__ == "__main__":
    main()
