"""
patch_hide_deactivated.py

Two fixes to commons/features.py:
1. get_profile() returns None (same as "user not found") for deactivated
   (is_active == False) users, instead of showing their profile/posts.
2. The following-feed excludes posts from deactivated authors, via a
   join to User.

Run once from your project root:
    python3 patch_hide_deactivated.py
"""

PATH = "commons/features.py"

# --- Fix 1: get_profile ---
PROFILE_ANCHOR = """        user = db.query(User).filter(User.username.ilike(username)).first()
        if not user:
            return None"""

PROFILE_NEW = """        user = db.query(User).filter(User.username.ilike(username)).first()
        if not user:
            return None
        if not user.is_active:
            return None"""

# --- Fix 2: following-feed ---
FEED_ANCHOR = """        return (
            db.query(Post)
            .filter(Post.author_id.in_(following_ids))
            .filter(Post.status == PostStatus.PUBLISHED)
            .order_by(desc(Post.published_at))
            .offset(offset)
            .limit(limit)
            .all()
        )"""

FEED_NEW = """        return (
            db.query(Post)
            .join(User, User.id == Post.author_id)
            .filter(Post.author_id.in_(following_ids))
            .filter(Post.status == PostStatus.PUBLISHED)
            .filter(User.is_active == True)
            .order_by(desc(Post.published_at))
            .offset(offset)
            .limit(limit)
            .all()
        )"""


def apply_patch(content, anchor, new, label):
    count = content.count(anchor)
    if count == 0:
        print(f"ERROR: anchor for '{label}' not found. Aborting before any write.")
        return None
    if count > 1:
        print(f"ERROR: anchor for '{label}' matched {count} times (expected 1). Aborting — needs manual review.")
        return None
    return content.replace(anchor, new, 1)


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "if not user.is_active:\n            return None" in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, PROFILE_ANCHOR, PROFILE_NEW, "get_profile is_active check")
    if content2 is None:
        return

    content3 = apply_patch(content2, FEED_ANCHOR, FEED_NEW, "following-feed is_active filter")
    if content3 is None:
        return

    with open(PATH, "w") as f:
        f.write(content3)

    print("Patched commons/features.py successfully.")


if __name__ == "__main__":
    main()
