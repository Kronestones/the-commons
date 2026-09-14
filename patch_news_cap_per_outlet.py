"""
patch_news_cap_per_outlet.py

Updates _news_visibility_filter so that following a news outlet only
surfaces their 3 most recent posts in the general feed, rather than
every post they've ever made. Prevents an active outlet from
dominating someone's feed the moment they follow it.

The outlet's own profile page is unaffected — this only limits what
appears in the general/home feed.

Run once from your project root:
    python3 patch_news_cap_per_outlet.py
"""

PATH = "commons/posts.py"

ANCHOR = '''    def _news_visibility_filter(self, db: Session, user: User):
        """
        News posts only show in the general feed to people who follow
        that outlet. Everyone else's feed stays free of headlines they
        never asked for — the outlet's own profile page is unaffected.
        """
        followed_ids = [
            f.following_id for f in
            db.query(Follow).filter(Follow.follower_id == user.id).all()
        ]
        return or_(
            Post.is_news == False,
            Post.author_id.in_(followed_ids) if followed_ids else False,
        )'''

NEW = '''    def _news_visibility_filter(self, db: Session, user: User):
        """
        News posts only show in the general feed to people who follow
        that outlet, and even then only their 3 most recent posts —
        following an active outlet shouldn't flood the feed. The
        outlet's own profile page is unaffected; this only limits
        what appears in the general/home feed.
        """
        RECENT_NEWS_PER_OUTLET = 3

        followed_ids = [
            f.following_id for f in
            db.query(Follow).filter(Follow.follower_id == user.id).all()
        ]

        allowed_news_post_ids = []
        if followed_ids:
            followed_news_authors = (
                db.query(User)
                .filter(User.id.in_(followed_ids))
                .all()
            )
            for author in followed_news_authors:
                recent = (
                    db.query(Post.id)
                    .filter(Post.author_id == author.id, Post.is_news == True)
                    .order_by(desc(Post.published_at))
                    .limit(RECENT_NEWS_PER_OUTLET)
                    .all()
                )
                allowed_news_post_ids.extend([r[0] for r in recent])

        return or_(
            Post.is_news == False,
            Post.id.in_(allowed_news_post_ids) if allowed_news_post_ids else False,
        )'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "allowed_news_post_ids" in content:
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

    print("Patched commons/posts.py successfully.")


if __name__ == "__main__":
    main()
