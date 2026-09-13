"""
patch_news_feed_visibility.py

News posts (is_news=True) should only appear in a user's main feed if
they follow that outlet's account — otherwise the feed gets flooded
with headlines nobody asked for. This adds a shared filter, applied
the same way _youth_filter already is across all three feed modes.

Outlet posts remain fully visible on the outlet's own profile page
regardless of this filter — this only affects the general/main feed.

Run once from your project root:
    python3 patch_news_feed_visibility.py
"""

PATH = "commons/posts.py"

IMPORT_ANCHOR = "from .database import (\n    Post, User, CommunityVote, FingerprintRecord,\n    PostStatus, PostType, AlgorithmMode\n)"
IMPORT_NEW = "from .database import (\n    Post, User, CommunityVote, FingerprintRecord,\n    PostStatus, PostType, AlgorithmMode\n)\nfrom .features import Follow\nfrom sqlalchemy import or_"

FILTER_ANCHOR = '''    def _youth_filter(self, user: User):
        """Extra content protection for minor accounts."""
        if user.is_minor:
            # Minors only see posts from verified, non-flagged authors
            # More protective content filtering applied
            return Post.is_political == False
        return True'''

FILTER_NEW = '''    def _youth_filter(self, user: User):
        """Extra content protection for minor accounts."""
        if user.is_minor:
            # Minors only see posts from verified, non-flagged authors
            # More protective content filtering applied
            return Post.is_political == False
        return True

    def _news_visibility_filter(self, db: Session, user: User):
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


def apply_patch(content, anchor, new, label):
    count = content.count(anchor)
    if count == 0:
        print(f"ERROR: anchor for '{label}' not found. Aborting before any write.")
        return None
    if count > 1:
        print(f"ERROR: anchor for '{label}' matched {count} times (expected 1). Aborting.")
        return None
    return content.replace(anchor, new, 1)


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "_news_visibility_filter" in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, IMPORT_ANCHOR, IMPORT_NEW, "imports")
    if content2 is None:
        return

    content3 = apply_patch(content2, FILTER_ANCHOR, FILTER_NEW, "news visibility filter")
    if content3 is None:
        return

    old_line = ".filter(self._youth_filter(user))"
    new_line = ".filter(self._youth_filter(user))\n            .filter(self._news_visibility_filter(db, user))"
    count = content3.count(old_line)
    if count != 3:
        print(f"WARNING: expected 3 occurrences of the youth filter line, found {count}. "
              f"Proceeding to replace all found — verify feed methods manually after this.")
    content4 = content3.replace(old_line, new_line)

    with open(PATH, "w") as f:
        f.write(content4)

    print(f"Patched commons/posts.py successfully ({count} feed methods updated).")


if __name__ == "__main__":
    main()
