"""
patch_main_bluesky_tiktok.py

Adds /api/profile/bluesky and /api/profile/tiktok routes to main.py,
matching the /api/profile/youtube route's shape.

Run once from your project root:
    python3 patch_main_bluesky_tiktok.py
"""

PATH = "main.py"

ANCHOR = '''@app.post("/api/profile/youtube")
async def api_update_youtube(
    youtube:      str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_youtube(db, current_user, youtube))'''

NEW = '''@app.post("/api/profile/youtube")
async def api_update_youtube(
    youtube:      str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_youtube(db, current_user, youtube))

@app.post("/api/profile/bluesky")
async def api_update_bluesky(
    bluesky:      str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_bluesky(db, current_user, bluesky))

@app.post("/api/profile/tiktok")
async def api_update_tiktok(
    tiktok:       str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_tiktok(db, current_user, tiktok))'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "/api/profile/bluesky" in content:
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

    print("Patched main.py successfully.")


if __name__ == "__main__":
    main()
