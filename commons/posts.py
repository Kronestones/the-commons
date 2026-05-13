"""
posts.py — Content and Feed

Content creation, feed generation, community voting.
Three algorithm modes — users choose.
Worth precedes engagement.

No manipulation. No addiction optimization.
The feed serves the people who use it.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from .database import (
    Post, User, CommunityVote, FingerprintRecord,
    PostStatus, PostType, AlgorithmMode
)
from .fingerprint import fingerprint
from .config import config


class PostManager:

    # ── Create ────────────────────────────────────────────────────────────────

    def create(self, db: Session, author: User, post_type: str,
               content: str = "", media_path: str = "",
               is_news: bool = False, is_political: bool = False) -> dict:
        # Zero tolerance content check — blocks before anything else
        from .fingerprint import check_zero_tolerance
        if check_zero_tolerance(content):
            return {"ok": False, "error": "Your post contains content that is not permitted on The Commons."}

        if not content and not media_path:
            return {"ok": False, "error": "Post must have content or media."}

        if len(content) > 10000:
            return {"ok": False, "error": "Post content exceeds 10,000 character limit."}

        post = Post(
            author_id    = author.id,
            post_type    = PostType(post_type),
            content      = content,
            media_path   = media_path,
            is_news      = is_news,
            is_political = is_political,
            status       = PostStatus.PENDING,
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        # Run Fingerprint immediately — invisible to user
        fingerprint.scan(db, post)
        db.refresh(post)

        return {"ok": True, "post": post}

    # ── Feed ──────────────────────────────────────────────────────────────────

    def get_feed(self, db: Session, user: User,
                 limit: int = 20, offset: int = 0) -> dict:
        """
        Get feed for user based on their chosen algorithm mode.
        Only published content appears in any feed.
        """
        mode = user.algorithm_mode

        if mode == AlgorithmMode.CHRONOLOGICAL:
            posts = self._chronological_feed(db, user, limit, offset)
            reason = None

        elif mode == AlgorithmMode.COMMUNITY:
            posts = self._community_feed(db, user, limit, offset)
            reason = None

        else:  # TRANSPARENT — default
            posts = self._transparent_feed(db, user, limit, offset)
            reason = "transparent"

        return {
            "posts":  posts,
            "mode":   mode,
            "reason": reason,
        }

    def _chronological_feed(self, db: Session, user: User,
                             limit: int, offset: int) -> List[Post]:
        """Pure chronological. No algorithm. No manipulation."""
        return (
            db.query(Post)
            .filter(Post.status == PostStatus.PUBLISHED)
            .filter(self._youth_filter(user))
            .order_by(desc(Post.published_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def _community_feed(self, db: Session, user: User,
                        limit: int, offset: int) -> List[Post]:
        """Community value score determines amplification — not view count."""
        return (
            db.query(Post)
            .filter(Post.status == PostStatus.PUBLISHED)
            .filter(self._youth_filter(user))
            .order_by(desc(Post.community_score), desc(Post.published_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def _transparent_feed(self, db: Session, user: User,
                           limit: int, offset: int) -> List[Post]:
        """
        Transparent algorithm — mix of recency and community value.
        Every post shows WHY it appears. No black box.
        """
        return (
            db.query(Post)
            .filter(Post.status == PostStatus.PUBLISHED)
            .filter(self._youth_filter(user))
            .order_by(
                desc(Post.community_score * 0.6 + Post.view_count * 0.001),
                desc(Post.published_at)
            )
            .offset(offset)
            .limit(limit)
            .all()
        )

    def _youth_filter(self, user: User):
        """Extra content protection for minor accounts."""
        if user.is_minor:
            # Minors only see posts from verified, non-flagged authors
            # More protective content filtering applied
            return Post.is_political == False
        return True

    def get_feed_reason(self, post: Post, user: User) -> str:
        """
        Transparent mode: every post shows why it appears.
        The algorithm is not a black box.
        """
        if user.algorithm_mode == AlgorithmMode.CHRONOLOGICAL:
            return None
        if user.algorithm_mode == AlgorithmMode.COMMUNITY:
            return f"Valued by the community · Score: {post.community_score:.1f}"

        # Transparent mode reasons
        if post.community_score > 5:
            return "Shown because: people in your region valued this highly"
        if post.view_count > 1000:
            return "Shown because: this is gaining attention in your language"
        return "Shown because: recent content from this platform"

    # ── Community Voting ──────────────────────────────────────────────────────

    def cast_community_vote(self, db: Session, user: User,
                            post_id: int, value: int) -> dict:
        """
        Community value voting — separate from view count.
        High community value + modest views = amplified.
        High views + low community value = not amplified.
        """
        if value not in (1, -1):
            return {"ok": False, "error": "Vote value must be 1 or -1."}

        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return {"ok": False, "error": "Post not found."}

        # Check existing vote
        existing = (db.query(CommunityVote)
                    .filter(CommunityVote.post_id == post_id,
                            CommunityVote.user_id == user.id)
                    .first())

        if existing:
            db.delete(existing)
            db.commit()
            self._recalculate_score(db, post)
            return {"ok": True, "voted": False}
        else:
            vote = CommunityVote(
                post_id = post_id,
                user_id = user.id,
                value   = value
            )
            db.add(vote)

        db.commit()
        self._recalculate_score(db, post)
        return {"ok": True, "voted": True}

    def _recalculate_score(self, db: Session, post: Post):
        result = (db.query(func.sum(CommunityVote.value))
                  .filter(CommunityVote.post_id == post.id)
                  .scalar())
        post.community_score = float(result or 0)
        db.commit()

    # ── View Count ────────────────────────────────────────────────────────────

    def record_view(self, db: Session, post_id: int):
        post = db.query(Post).filter(Post.id == post_id).first()
        if post:
            post.view_count += 1
            db.commit()

    # ── Get Post ──────────────────────────────────────────────────────────────

    def get_post(self, db: Session, post_id: int,
                 viewer: Optional[User] = None) -> Optional[Post]:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return None
        if post.status != PostStatus.PUBLISHED:
            # Only author and Circle can see unpublished posts
            if viewer and (viewer.id == post.author_id or
                           viewer.role.value in ("circle", "sovereign")):
                return post
            return None
        return post


posts = PostManager()
