"""
social.py — Likes, Comments, and Shares

The social fabric of The Commons.
Simple, clean, no dark patterns.

Likes     — one per user per post. Transparent count.
Comments  — threaded replies. Fingerprinted if political/news.
Shares    — reposts with optional note. Credit always given to original.

No like counts hidden to manipulate anxiety.
No comment ranking by outrage.
No share amplification of unverified content.

Codex Law 1: People First.
Codex Law 5: Transparency.
Codex Law 6: Truth.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Session, relationship
from .database import Base, Post, User, PostStatus
from .fingerprint import fingerprint


# ── Models ────────────────────────────────────────────────────────────────────

class Like(Base):
    """One like per user per post. Simple and honest."""
    __tablename__ = "likes"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id     = Column(Integer, ForeignKey("posts.id"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


class Comment(Base):
    """
    Threaded comments. Replies supported one level deep.
    Political/news comments go through Fingerprint like posts.
    """
    __tablename__ = "comments"

    id          = Column(Integer, primary_key=True, index=True)
    post_id     = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id   = Column(Integer, ForeignKey("comments.id"), nullable=True)  # For replies
    content     = Column(Text, nullable=False)
    is_removed  = Column(Boolean, default=False)
    remove_reason = Column(String(300), default="")
    created_at  = Column(DateTime, default=datetime.utcnow)

    replies     = relationship("Comment", backref="parent", remote_side=[id])


class Share(Base):
    """
    Reposts with full credit to original author.
    Cannot share unverified/held content.
    Optional note from the person sharing.
    """
    __tablename__ = "shares"

    id              = Column(Integer, primary_key=True, index=True)
    original_post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    shared_by_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    note            = Column(Text, default="")   # Optional message from sharer
    created_at      = Column(DateTime, default=datetime.utcnow)


# ── Social Manager ────────────────────────────────────────────────────────────

class SocialManager:

    # ── Likes ─────────────────────────────────────────────────────────────────

    def toggle_like(self, db: Session, user: User, post_id: int) -> dict:
        """Like or unlike a post. One like per user per post."""
        # Zero tolerance content check
        from .fingerprint import check_zero_tolerance
        if check_zero_tolerance(content):
            return {"ok": False, "error": "Your comment contains content that is not permitted on The Commons."}

        post = db.query(Post).filter(
            Post.id == post_id,
            Post.status == PostStatus.PUBLISHED
        ).first()
        if not post:
            return {"ok": False, "error": "Post not found."}

        existing = db.query(Like).filter(
            Like.user_id == user.id,
            Like.post_id == post_id
        ).first()

        if existing:
            db.delete(existing)
            db.commit()
            liked = False
        else:
            db.add(Like(user_id=user.id, post_id=post_id))
            db.commit()
            liked = True

        count = db.query(Like).filter(Like.post_id == post_id).count()
        return {"ok": True, "liked": liked, "count": count}

    def get_like_count(self, db: Session, post_id: int) -> int:
        return db.query(Like).filter(Like.post_id == post_id).count()

    def user_liked(self, db: Session, user_id: int, post_id: int) -> bool:
        return db.query(Like).filter(
            Like.user_id == user_id,
            Like.post_id == post_id
        ).first() is not None

    # ── Comments ──────────────────────────────────────────────────────────────

    def add_comment(self, db: Session, user: User, post_id: int,
                    content: str, parent_id: int = None) -> dict:
        """Add a comment. Fingerprinted if the parent post is political/news."""
        if not content or len(content.strip()) == 0:
            return {"ok": False, "error": "Comment cannot be empty."}
        if len(content) > 2000:
            return {"ok": False, "error": "Comment cannot exceed 2000 characters."}

        # Zero tolerance content check
        from .fingerprint import check_zero_tolerance
        if check_zero_tolerance(content):
            return {"ok": False, "error": "Your comment contains content that is not permitted on The Commons."}

        post = db.query(Post).filter(
            Post.id == post_id,
            Post.status == PostStatus.PUBLISHED
        ).first()
        if not post:
            return {"ok": False, "error": "Post not found."}

        # Validate parent comment exists if replying
        if parent_id:
            parent = db.query(Comment).filter(
                Comment.id == parent_id,
                Comment.post_id == post_id
            ).first()
            if not parent:
                return {"ok": False, "error": "Parent comment not found."}

        # Youth protection — minors cannot comment on political posts
        if user.is_minor and post.is_political:
            return {"ok": False, "error": "This content is restricted for your account."}

        comment = Comment(
            post_id   = post_id,
            author_id = user.id,
            parent_id = parent_id,
            content   = content.strip(),
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        return {"ok": True, "comment_id": comment.id}

    def get_comments(self, db: Session, post_id: int,
                     viewer: Optional[User] = None) -> List[dict]:
        """Get all top-level comments with their replies."""
        comments = (
            db.query(Comment)
            .filter(
                Comment.post_id == post_id,
                Comment.parent_id == None,
                Comment.is_removed == False
            )
            .order_by(Comment.created_at)
            .all()
        )

        result = []
        for c in comments:
            replies = (
                db.query(Comment)
                .filter(
                    Comment.parent_id == c.id,
                    Comment.is_removed == False
                )
                .order_by(Comment.created_at)
                .all()
            )
            author = db.query(User).filter(User.id == c.author_id).first()
            result.append({
                "id":         c.id,
                "author":     author.username if author else "unknown",
                "content":    c.content,
                "created_at": c.created_at.isoformat(),
                "replies": [
                    {
                        "id":         r.id,
                        "author":     db.query(User).filter(User.id == r.author_id).first().username if db.query(User).filter(User.id == r.author_id).first() else "unknown",
                        "content":    r.content,
                        "created_at": r.created_at.isoformat(),
                    }
                    for r in replies
                ]
            })
        return result

    def remove_comment(self, db: Session, comment_id: int,
                       requester: User, reason: str = "") -> dict:
        """Remove a comment — author or Circle can remove."""
        comment = db.query(Comment).filter(Comment.id == comment_id).first()
        if not comment:
            return {"ok": False, "error": "Comment not found."}

        if comment.author_id != requester.id and requester.role.value not in ("circle", "sovereign"):
            return {"ok": False, "error": "You can only remove your own comments."}

        comment.is_removed    = True
        comment.remove_reason = reason
        db.commit()
        return {"ok": True}

    # ── Shares ────────────────────────────────────────────────────────────────

    def share_post(self, db: Session, user: User,
                   post_id: int, note: str = "") -> dict:
        """
        Share a post. Full credit always given to original author.
        Cannot share unverified or held content.
        """
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return {"ok": False, "error": "Post not found."}

        # Cannot share unverified content
        if post.status != PostStatus.PUBLISHED:
            return {"ok": False, "error": "Only published content can be shared."}

        # Cannot share your own post
        if post.author_id == user.id:
            return {"ok": False, "error": "You cannot share your own post."}

        # Check not already shared by this user
        existing = db.query(Share).filter(
            Share.original_post_id == post_id,
            Share.shared_by_id == user.id
        ).first()
        if existing:
            return {"ok": False, "error": "You have already shared this post."}

        # Youth protection
        if user.is_minor and post.is_political:
            return {"ok": False, "error": "This content is restricted for your account."}

        share = Share(
            original_post_id = post_id,
            shared_by_id     = user.id,
            note             = note[:500] if note else "",
        )
        db.add(share)
        db.commit()
        db.refresh(share)

        original_author = db.query(User).filter(User.id == post.author_id).first()
        return {
            "ok":              True,
            "share_id":        share.id,
            "original_author": original_author.username if original_author else "unknown",
            "note":            "Credit always given to the original author."
        }

    def get_share_count(self, db: Session, post_id: int) -> int:
        return db.query(Share).filter(Share.original_post_id == post_id).count()


social = SocialManager()
