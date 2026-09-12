"""
patch_main_youtube.py

Adds /api/profile/youtube route to main.py, matching the
/api/profile/spotify route's shape.

Run once from your project root:
    python3 patch_main_youtube.py
"""

PATH = "main.py"

ANCHOR = """@app.post("/api/profile/spotify")
async def api_update_spotify(
    spotify:      str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_spotify(db, current_user, spotify))"""

NEW_ROUTE = """

@app.post("/api/profile/youtube")
async def api_update_youtube(
    youtube:      str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_youtube(db, current_user, youtube))"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "/api/profile/youtube" in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting.")
        return

    content = content.replace(ANCHOR, ANCHOR + NEW_ROUTE, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched main.py successfully.")


if __name__ == "__main__":
    main()
