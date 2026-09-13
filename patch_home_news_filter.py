"""
patch_home_news_filter.py

The home() route in main.py has its own separate query for the first
20 posts shown on initial page load — completely bypassing
PostManager.get_feed() and the news visibility filter added there
earlier. This applies the same filter directly to that query.

Run once from your project root:
    python3 patch_home_news_filter.py
"""

PATH = "main.py"

ANCHOR = """    # Get recent published posts for the landing feed
    recent_posts = (
        db.query(Post)
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(Post.published_at.desc())
        .limit(20)
        .all()
    )
    # Decode token from cookie for template use
    from commons.auth import decode_token
    from commons.database import CommunityVote
    current_username = None
    voted_post_ids = set()
    token = request.cookies.get("token", "")
    if token:
        payload = decode_token(token)
        if payload:
            current_username = payload.get("username")
            user_id = int(payload.get("sub", 0))
            post_ids = [p.id for p in recent_posts]"""

NEW = """    # Decode token from cookie for template use
    from commons.auth import decode_token
    from commons.database import CommunityVote, User
    current_username = None
    voted_post_ids = set()
    home_user = None
    token = request.cookies.get("token", "")
    if token:
        payload = decode_token(token)
        if payload:
            current_username = payload.get("username")
            user_id = int(payload.get("sub", 0))
            home_user = db.query(User).filter(User.id == user_id).first()

    # Get recent published posts for the landing feed — same news
    # visibility rule as the main feed: news posts only show here if
    # the viewer follows that outlet.
    recent_posts_query = (
        db.query(Post)
        .filter(Post.status == PostStatus.PUBLISHED)
    )
    if home_user:
        recent_posts_query = recent_posts_query.filter(
            posts._news_visibility_filter(db, home_user)
        )
    else:
        recent_posts_query = recent_posts_query.filter(Post.is_news == False)

    recent_posts = (
        recent_posts_query
        .order_by(Post.published_at.desc())
        .limit(20)
        .all()
    )

    if token:
        payload = decode_token(token)
        if payload:
            user_id = int(payload.get("sub", 0))
            post_ids = [p.id for p in recent_posts]"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "_news_visibility_filter(db, home_user)" in content:
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

    print("Patched main.py successfully.")


if __name__ == "__main__":
    main()
