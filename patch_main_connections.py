"""
patch_main_connections.py

Adds /api/profile/twitch and /api/profile/spotify routes to main.py,
matching the existing /api/profile/bio route's shape.

Run once from your project root:
    python3 patch_main_connections.py
"""

PATH = "main.py"

ANCHOR = """@app.post("/api/profile/bio")
async def api_update_bio(
    bio:          str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_bio(db, current_user, bio))"""

NEW_ROUTES = """

@app.post("/api/profile/twitch")
async def api_update_twitch(
    twitch:       str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_twitch(db, current_user, twitch))

@app.post("/api/profile/spotify")
async def api_update_spotify(
    spotify:      str = Form(""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_spotify(db, current_user, spotify))"""

def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "/api/profile/twitch" in content:
        print("Already patched — no changes made.")
        return

    if ANCHOR not in content:
        print("ERROR: anchor block not found. File may have changed — aborting, nothing written.")
        return

    content = content.replace(ANCHOR, ANCHOR + NEW_ROUTES, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched main.py successfully.")

if __name__ == "__main__":
    main()
