"""
patch_add_explore_route.py

Adds two routes to main.py:
1. GET /explore — renders the explore page template
2. GET /api/explore/outlets — returns each news outlet's latest post
   and whether the current user follows them

Run once from your project root:
    python3 patch_add_explore_route.py
"""

PATH = "main.py"

ANCHOR = '''@app.post("/api/users/{user_id}/follow_by_id")
async def api_follow(
    user_id:      int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = follow_manager.toggle_follow(db, current_user, user_id)
    return JSONResponse(result)'''

NEW = '''@app.post("/api/users/{user_id}/follow_by_id")
async def api_follow(
    user_id:      int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = follow_manager.toggle_follow(db, current_user, user_id)
    return JSONResponse(result)

@app.get("/explore", response_class=HTMLResponse)
async def explore_page(request: Request):
    return templates.TemplateResponse("explore.html", {"request": request})

@app.get("/api/explore/outlets")
async def api_explore_outlets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.news_feed import NEWS_OUTLETS
    from sqlalchemy import desc
    outlets_data = []
    for outlet in NEWS_OUTLETS:
        outlet_user = db.query(User).filter(
            User.username.ilike(outlet["username"])
        ).first()
        if not outlet_user or not outlet_user.is_active:
            continue

        latest = (
            db.query(Post)
            .filter(Post.author_id == outlet_user.id, Post.status == PostStatus.PUBLISHED)
            .order_by(desc(Post.published_at))
            .first()
        )

        outlets_data.append({
            "id":           outlet_user.id,
            "username":     outlet_user.username,
            "is_following": follow_manager.is_following(db, current_user.id, outlet_user.id),
            "latest_post":  (latest.content[:200] if latest else None),
        })

    return JSONResponse({"ok": True, "outlets": outlets_data})'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "/api/explore/outlets" in content:
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
