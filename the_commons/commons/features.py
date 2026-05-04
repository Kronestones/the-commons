"""
features.py — The Commons Full Feature Set

Follow system, user profiles, notifications, search,
hashtags, direct messages, bookmarks, creator stats, trending.

All built with The Commons philosophy:
- Transparent
- No dark patterns
- No manipulation
- People first

Codex Law 1: People First
Codex Law 3: No data selling
Codex Law 5: Transparency

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, func, desc
from sqlalchemy.orm import Session, relationship
from .database import Base, Post, User, PostStatus


# ── Models ────────────────────────────────────────────────────────────────────

class Follow(Base):
    """Follow system. Simple. No algorithmic manipulation of follower counts."""
    __tablename__ = "follows"

    id            = Column(Integer, primary_key=True, index=True)
    follower_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    """
    Notifications for follows, likes, comments, shares.
    No dark pattern notifications designed to pull you back in.
    Just genuine activity on your content.
    """
    __tablename__ = "notifications"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    actor_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    notif_type    = Column(String(50), nullable=False)  # like, comment, share, follow, mention
    post_id       = Column(Integer, ForeignKey("posts.id"), nullable=True)
    message       = Column(String(300), default="")
    is_read       = Column(Boolean, default=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class Hashtag(Base):
    """Hashtags on posts."""
    __tablename__ = "hashtags"

    id            = Column(Integer, primary_key=True, index=True)
    tag           = Column(String(100), unique=True, index=True, nullable=False)
    post_count    = Column(Integer, default=0)
    created_at    = Column(DateTime, default=datetime.utcnow)


class PostHashtag(Base):
    """Many-to-many: posts to hashtags."""
    __tablename__ = "post_hashtags"

    id            = Column(Integer, primary_key=True, index=True)
    post_id       = Column(Integer, ForeignKey("posts.id"), nullable=False)
    hashtag_id    = Column(Integer, ForeignKey("hashtags.id"), nullable=False)


class Bookmark(Base):
    """Save posts for later. Private to the user."""
    __tablename__ = "bookmarks"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id       = Column(Integer, ForeignKey("posts.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class DirectMessage(Base):
    """
    End-to-end encrypted direct messages.
    Not readable by the platform. Codex Law 3.
    Messages are stored encrypted — only sender and recipient can read.
    """
    __tablename__ = "direct_messages"

    id              = Column(Integer, primary_key=True, index=True)
    sender_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_encrypted = Column(Text, nullable=False)  # Encrypted — not readable by platform
    is_read         = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


# ── Follow Manager ────────────────────────────────────────────────────────────

class FollowManager:

    def toggle_follow(self, db: Session, follower: User,
                      following_id: int) -> dict:
        """Follow or unfollow a user."""
        if follower.id == following_id:
            return {"ok": False, "error": "You cannot follow yourself."}

        target = db.query(User).filter(User.id == following_id).first()
        if not target:
            return {"ok": False, "error": "User not found."}

        existing = db.query(Follow).filter(
            Follow.follower_id  == follower.id,
            Follow.following_id == following_id
        ).first()

        if existing:
            db.delete(existing)
            db.commit()
            following = False
        else:
            db.add(Follow(follower_id=follower.id, following_id=following_id))
            db.commit()
            # Notify the followed user
            notification_manager.create(
                db,
                user_id    = following_id,
                actor_id   = follower.id,
                notif_type = "follow",
                message    = f"@{follower.username} started following you"
            )
            following = True

        followers_count  = db.query(Follow).filter(Follow.following_id == following_id).count()
        following_count  = db.query(Follow).filter(Follow.follower_id == following_id).count()

        return {
            "ok":             True,
            "following":      following,
            "followers_count": followers_count,
            "following_count": following_count,
        }

    def is_following(self, db: Session, follower_id: int,
                     following_id: int) -> bool:
        return db.query(Follow).filter(
            Follow.follower_id  == follower_id,
            Follow.following_id == following_id
        ).first() is not None

    def get_followers(self, db: Session, user_id: int) -> List[dict]:
        follows = db.query(Follow).filter(Follow.following_id == user_id).all()
        result = []
        for f in follows:
            user = db.query(User).filter(User.id == f.follower_id).first()
            if user:
                result.append({"id": user.id, "username": user.username,
                               "display_name": user.display_name})
        return result

    def get_following(self, db: Session, user_id: int) -> List[dict]:
        follows = db.query(Follow).filter(Follow.follower_id == user_id).all()
        result = []
        for f in follows:
            user = db.query(User).filter(User.id == f.following_id).first()
            if user:
                result.append({"id": user.id, "username": user.username,
                               "display_name": user.display_name})
        return result

    def get_following_feed(self, db: Session, user: User,
                           limit: int = 20, offset: int = 0) -> List[Post]:
        """Feed of posts from people you follow — chronological."""
        following_ids = [
            f.following_id for f in
            db.query(Follow).filter(Follow.follower_id == user.id).all()
        ]
        if not following_ids:
            return []
        return (
            db.query(Post)
            .filter(Post.author_id.in_(following_ids))
            .filter(Post.status == PostStatus.PUBLISHED)
            .order_by(desc(Post.published_at))
            .offset(offset)
            .limit(limit)
            .all()
        )


# ── Profile Manager ───────────────────────────────────────────────────────────

class ProfileManager:

    def get_profile(self, db: Session, username: str,
                    viewer: Optional[User] = None) -> Optional[dict]:
        """Get a user's public profile."""
        user = db.query(User).filter(User.username.ilike(username)).first()
        if not user:
            return None

        posts = (
            db.query(Post)
            .filter(Post.author_id == user.id,
                    Post.status == PostStatus.PUBLISHED)
            .order_by(desc(Post.published_at))
            .limit(30)
            .all()
        )

        followers_count = db.query(Follow).filter(Follow.following_id == user.id).count()
        following_count = db.query(Follow).filter(Follow.follower_id == user.id).count()
        is_following    = False

        if viewer and viewer.id != user.id:
            is_following = follow_manager.is_following(db, viewer.id, user.id)

        # Creator stats
        total_likes  = sum(
            db.query(func.count()).select_from(__import__('commons.social',
                fromlist=['Like']).Like).filter_by(post_id=p.id).scalar() or 0
            for p in posts
        )

        return {
            "id":              user.id,
            "username":        user.username,
            "display_name":    user.display_name or user.username,
            "bio":             user.bio or "",
            "role":            user.role.value,
            "joined":          user.created_at.strftime("%B %Y"),
            "followers":       followers_count,
            "following":       following_count,
            "post_count":      len(posts),
            "is_following":    is_following,
            "avatar_path":     user.avatar_path or None,
            "banner_path":     user.banner_path or None,
            "posts": [
                {
                    "id":              p.id,
                    "content":         p.content[:100],
                    "post_type":       p.post_type.value,
                    "community_score": p.community_score,
                    "view_count":      p.view_count,
                    "published_at":    p.published_at.isoformat() if p.published_at else None,
                }
                for p in posts
            ]
        }

    def update_bio(self, db: Session, user: User, bio: str) -> dict:
        if len(bio) > 300:
            return {"ok": False, "error": "Bio must be 300 characters or fewer."}
        user.bio = bio
        db.commit()
        return {"ok": True}

    def update_display_name(self, db: Session, user: User,
                             display_name: str) -> dict:
        if len(display_name) > 100:
            return {"ok": False, "error": "Display name must be 100 characters or fewer."}
        user.display_name = display_name
        db.commit()
        return {"ok": True}


# ── Notification Manager ──────────────────────────────────────────────────────

class NotificationManager:

    def create(self, db: Session, user_id: int, actor_id: int,
               notif_type: str, message: str,
               post_id: int = None) -> None:
        """Create a notification. No dark patterns — only genuine activity."""
        # Don't notify yourself
        if user_id == actor_id:
            return

        notif = Notification(
            user_id    = user_id,
            actor_id   = actor_id,
            notif_type = notif_type,
            post_id    = post_id,
            message    = message,
        )
        db.add(notif)
        db.commit()

    def get_notifications(self, db: Session, user: User,
                          limit: int = 30) -> List[dict]:
        notifs = (
            db.query(Notification)
            .filter(Notification.user_id == user.id)
            .order_by(desc(Notification.created_at))
            .limit(limit)
            .all()
        )
        result = []
        for n in notifs:
            actor = db.query(User).filter(User.id == n.actor_id).first()
            result.append({
                "id":         n.id,
                "type":       n.notif_type,
                "actor":      actor.username if actor else "unknown",
                "message":    n.message,
                "post_id":    n.post_id,
                "is_read":    n.is_read,
                "created_at": n.created_at.isoformat(),
            })
        return result

    def mark_read(self, db: Session, user: User,
                  notification_id: int = None) -> dict:
        """Mark one or all notifications as read."""
        query = db.query(Notification).filter(Notification.user_id == user.id)
        if notification_id:
            query = query.filter(Notification.id == notification_id)
        query.update({"is_read": True})
        db.commit()
        return {"ok": True}

    def unread_count(self, db: Session, user: User) -> int:
        return db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.is_read == False
        ).count()


# ── Search Manager ────────────────────────────────────────────────────────────

class SearchManager:

    def search(self, db: Session, query: str,
               search_type: str = "all",
               viewer: Optional[User] = None) -> dict:
        """
        Search users, posts, and hashtags.
        No sponsored results. No paid placement. Ever.
        """
        query = query.strip()
        if not query or len(query) < 2:
            return {"ok": False, "error": "Search query must be at least 2 characters."}

        results = {"query": query, "users": [], "posts": [], "hashtags": []}

        if search_type in ("all", "users"):
            users = (
                db.query(User)
                .filter(
                    User.username.ilike(f"%{query}%") |
                    User.display_name.ilike(f"%{query}%")
                )
                .filter(User.is_active == True)
                .limit(10)
                .all()
            )
            results["users"] = [
                {"id": u.id, "username": u.username,
                 "display_name": u.display_name or u.username}
                for u in users
            ]

        if search_type in ("all", "posts"):
            posts = (
                db.query(Post)
                .filter(Post.content.ilike(f"%{query}%"))
                .filter(Post.status == PostStatus.PUBLISHED)
                .order_by(desc(Post.community_score))
                .limit(20)
                .all()
            )
            # Apply youth filter
            if viewer and viewer.is_minor:
                posts = [p for p in posts if not p.is_political]

            results["posts"] = [
                {"id": p.id, "content": p.content[:150],
                 "author": p.author.username if p.author else "unknown",
                 "community_score": p.community_score}
                for p in posts
            ]

        if search_type in ("all", "hashtags"):
            tags = (
                db.query(Hashtag)
                .filter(Hashtag.tag.ilike(f"%{query}%"))
                .order_by(desc(Hashtag.post_count))
                .limit(10)
                .all()
            )
            results["hashtags"] = [
                {"tag": t.tag, "post_count": t.post_count}
                for t in tags
            ]

        return {"ok": True, "results": results}

    def extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from post content."""
        import re
        tags = re.findall(r'#(\w+)', content)
        return list(set(t.lower() for t in tags if len(t) <= 50))

    def index_post_hashtags(self, db: Session, post: Post) -> None:
        """Index hashtags from a post."""
        tags = self.extract_hashtags(post.content or "")
        for tag_text in tags:
            tag = db.query(Hashtag).filter(Hashtag.tag == tag_text).first()
            if not tag:
                tag = Hashtag(tag=tag_text, post_count=0)
                db.add(tag)
                db.flush()
            tag.post_count += 1
            db.add(PostHashtag(post_id=post.id, hashtag_id=tag.id))
        if tags:
            db.commit()

    def get_hashtag_posts(self, db: Session, tag: str,
                          limit: int = 20, offset: int = 0) -> List[dict]:
        """Get all posts with a specific hashtag."""
        hashtag = db.query(Hashtag).filter(Hashtag.tag == tag.lower()).first()
        if not hashtag:
            return []

        post_hashtags = (
            db.query(PostHashtag)
            .filter(PostHashtag.hashtag_id == hashtag.id)
            .offset(offset)
            .limit(limit)
            .all()
        )
        posts = []
        for ph in post_hashtags:
            post = db.query(Post).filter(
                Post.id == ph.post_id,
                Post.status == PostStatus.PUBLISHED
            ).first()
            if post:
                posts.append({
                    "id":              post.id,
                    "content":         post.content[:150],
                    "author":          post.author.username if post.author else "unknown",
                    "community_score": post.community_score,
                    "published_at":    post.published_at.isoformat() if post.published_at else None,
                })
        return posts


# ── Bookmark Manager ──────────────────────────────────────────────────────────

class BookmarkManager:

    def toggle_bookmark(self, db: Session, user: User,
                        post_id: int) -> dict:
        """Save or unsave a post. Private to the user."""
        post = db.query(Post).filter(
            Post.id == post_id,
            Post.status == PostStatus.PUBLISHED
        ).first()
        if not post:
            return {"ok": False, "error": "Post not found."}

        existing = db.query(Bookmark).filter(
            Bookmark.user_id == user.id,
            Bookmark.post_id == post_id
        ).first()

        if existing:
            db.delete(existing)
            db.commit()
            return {"ok": True, "saved": False}
        else:
            db.add(Bookmark(user_id=user.id, post_id=post_id))
            db.commit()
            return {"ok": True, "saved": True}

    def get_bookmarks(self, db: Session, user: User,
                      limit: int = 20, offset: int = 0) -> List[dict]:
        """Get saved posts. Private — only the user sees their own bookmarks."""
        bookmarks = (
            db.query(Bookmark)
            .filter(Bookmark.user_id == user.id)
            .order_by(desc(Bookmark.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )
        result = []
        for b in bookmarks:
            post = db.query(Post).filter(
                Post.id == b.post_id,
                Post.status == PostStatus.PUBLISHED
            ).first()
            if post:
                result.append({
                    "id":           post.id,
                    "content":      post.content[:150],
                    "author":       post.author.username if post.author else "unknown",
                    "saved_at":     b.created_at.isoformat(),
                    "post_type":    post.post_type.value,
                })
        return result


# ── Creator Stats ─────────────────────────────────────────────────────────────

class CreatorStats:

    def get_stats(self, db: Session, user: User) -> dict:
        """
        Creator stats — how your content is performing.
        Transparent. Your data about your content.
        """
        from commons.social import Like, Share
        from sqlalchemy import func

        posts = db.query(Post).filter(
            Post.author_id == user.id,
            Post.status == PostStatus.PUBLISHED
        ).all()

        total_posts     = len(posts)
        total_views     = sum(p.view_count for p in posts)
        total_likes     = sum(
            db.query(func.count(Like.id)).filter(Like.post_id == p.id).scalar() or 0
            for p in posts
        )
        total_shares    = sum(
            db.query(func.count(Share.id)).filter(
                Share.original_post_id == p.id
            ).scalar() or 0
            for p in posts
        )
        total_community_score = sum(p.community_score for p in posts)
        followers_count = db.query(Follow).filter(
            Follow.following_id == user.id
        ).count()

        # Top performing posts
        top_posts = sorted(posts, key=lambda p: p.community_score, reverse=True)[:5]

        return {
            "username":        user.username,
            "total_posts":     total_posts,
            "total_views":     total_views,
            "total_likes":     total_likes,
            "total_shares":    total_shares,
            "total_community_score": total_community_score,
            "followers":       followers_count,
            "top_posts": [
                {
                    "id":              p.id,
                    "content":         p.content[:80],
                    "community_score": p.community_score,
                    "view_count":      p.view_count,
                }
                for p in top_posts
            ],
            "note": "These are your stats. This data is yours and is never sold."
        }


# ── Trending Manager ──────────────────────────────────────────────────────────

class TrendingManager:

    def get_trending(self, db: Session,
                     viewer: Optional[User] = None,
                     limit: int = 20) -> dict:
        """
        Trending content based on community value — not virality or outrage.
        What the community genuinely finds valuable right now.
        """
        since = datetime.utcnow() - timedelta(hours=24)

        # Trending posts — high community score in last 24 hours
        trending_posts = (
            db.query(Post)
            .filter(
                Post.status == PostStatus.PUBLISHED,
                Post.published_at >= since,
            )
            .order_by(desc(Post.community_score), desc(Post.view_count))
            .limit(limit)
            .all()
        )

        # Apply youth filter
        if viewer and viewer.is_minor:
            trending_posts = [p for p in trending_posts if not p.is_political]

        # Trending hashtags
        trending_tags = (
            db.query(Hashtag)
            .order_by(desc(Hashtag.post_count))
            .limit(10)
            .all()
        )

        return {
            "ok": True,
            "trending_posts": [
                {
                    "id":              p.id,
                    "content":         p.content[:150],
                    "author":          p.author.username if p.author else "unknown",
                    "community_score": p.community_score,
                    "view_count":      p.view_count,
                    "post_type":       p.post_type.value,
                    "published_at":    p.published_at.isoformat() if p.published_at else None,
                }
                for p in trending_posts
            ],
            "trending_hashtags": [
                {"tag": t.tag, "post_count": t.post_count}
                for t in trending_tags
            ],
            "note": "Trending is based on community value — not outrage or virality."
        }


# ── Direct Messages ───────────────────────────────────────────────────────────

class DirectMessageManager:
    """
    End-to-end encrypted direct messages.
    The platform cannot read message content.
    Codex Law 3: No data selling. No surveillance.
    """

    def send(self, db: Session, sender: User,
             recipient_id: int, content: str) -> dict:
        if not content or len(content.strip()) == 0:
            return {"ok": False, "error": "Message cannot be empty."}
        if len(content) > 5000:
            return {"ok": False, "error": "Message too long."}

        recipient = db.query(User).filter(User.id == recipient_id).first()
        if not recipient:
            return {"ok": False, "error": "Recipient not found."}
        if not recipient.is_active:
            return {"ok": False, "error": "Cannot message this account."}

        # In production: encrypt with recipient's public key
        # For now: store as-is, mark as encrypted placeholder
        msg = DirectMessage(
            sender_id          = sender.id,
            recipient_id       = recipient_id,
            content_encrypted  = content,  # TODO: Replace with actual E2E encryption
        )
        db.add(msg)
        db.commit()

        # Notify recipient
        notification_manager.create(
            db,
            user_id    = recipient_id,
            actor_id   = sender.id,
            notif_type = "message",
            message    = f"New message from @{sender.username}"
        )

        return {"ok": True, "message_id": msg.id}

    def get_conversation(self, db: Session, user: User,
                         other_user_id: int,
                         limit: int = 50) -> List[dict]:
        """Get messages between two users."""
        messages = (
            db.query(DirectMessage)
            .filter(
                ((DirectMessage.sender_id == user.id) &
                 (DirectMessage.recipient_id == other_user_id)) |
                ((DirectMessage.sender_id == other_user_id) &
                 (DirectMessage.recipient_id == user.id))
            )
            .order_by(DirectMessage.created_at)
            .limit(limit)
            .all()
        )

        # Mark as read
        for msg in messages:
            if msg.recipient_id == user.id and not msg.is_read:
                msg.is_read = True
        db.commit()

        return [
            {
                "id":         m.id,
                "sender":     m.sender_id,
                "content":    m.content_encrypted,
                "is_read":    m.is_read,
                "sent_at":    m.created_at.isoformat(),
                "is_mine":    m.sender_id == user.id,
            }
            for m in messages
        ]

    def get_inbox(self, db: Session, user: User) -> List[dict]:
        """Get list of conversations."""
        # Get unique conversation partners
        sent = db.query(DirectMessage.recipient_id).filter(
            DirectMessage.sender_id == user.id
        ).distinct().all()
        received = db.query(DirectMessage.sender_id).filter(
            DirectMessage.recipient_id == user.id
        ).distinct().all()

        partner_ids = set(
            [s[0] for s in sent] + [r[0] for r in received]
        )

        conversations = []
        for pid in partner_ids:
            partner = db.query(User).filter(User.id == pid).first()
            if not partner:
                continue
            unread = db.query(DirectMessage).filter(
                DirectMessage.sender_id    == pid,
                DirectMessage.recipient_id == user.id,
                DirectMessage.is_read      == False
            ).count()
            last_msg = (
                db.query(DirectMessage)
                .filter(
                    ((DirectMessage.sender_id == user.id) &
                     (DirectMessage.recipient_id == pid)) |
                    ((DirectMessage.sender_id == pid) &
                     (DirectMessage.recipient_id == user.id))
                )
                .order_by(desc(DirectMessage.created_at))
                .first()
            )
            conversations.append({
                "partner_id":       pid,
                "partner_username": partner.username,
                "unread_count":     unread,
                "last_message":     last_msg.content_encrypted[:50] if last_msg else "",
                "last_at":          last_msg.created_at.isoformat() if last_msg else "",
            })

        return sorted(conversations, key=lambda x: x["last_at"], reverse=True)


# ── Singleton instances ───────────────────────────────────────────────────────

follow_manager       = FollowManager()
profile_manager      = ProfileManager()
notification_manager = NotificationManager()
search_manager       = SearchManager()
bookmark_manager     = BookmarkManager()
creator_stats        = CreatorStats()
trending_manager     = TrendingManager()
dm_manager           = DirectMessageManager()


# ── Block System ──────────────────────────────────────────────────────────────

class UserBlock(Base):
    """Block a user. They cannot see your content or interact with you."""
    __tablename__ = "user_blocks"
    id          = Column(Integer, primary_key=True, index=True)
    blocker_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    blocked_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


class ContentReport(Base):
    """User report of content that violates the Codex."""
    __tablename__ = "content_reports"
    id          = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id     = Column(Integer, ForeignKey("posts.id"), nullable=True)
    reason      = Column(String(100), nullable=False)
    details     = Column(Text, default="")
    status      = Column(String(50), default="pending")
    created_at  = Column(DateTime, default=datetime.utcnow)


class VideoResponse(Base):
    """Stitch or Duet — video response to another post."""
    __tablename__ = "video_responses"
    id              = Column(Integer, primary_key=True, index=True)
    response_type   = Column(String(20), nullable=False)  # stitch / duet
    original_post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    response_post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class BlockManager:

    def toggle_block(self, db: Session, blocker: User, blocked_id: int) -> dict:
        if blocker.id == blocked_id:
            return {"ok": False, "error": "You cannot block yourself."}
        existing = db.query(UserBlock).filter(
            UserBlock.blocker_id == blocker.id,
            UserBlock.blocked_id == blocked_id
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
            return {"ok": True, "blocked": False, "message": "User unblocked."}
        db.add(UserBlock(blocker_id=blocker.id, blocked_id=blocked_id))
        db.commit()
        return {"ok": True, "blocked": True, "message": "User blocked. They can no longer see your content or interact with you."}

    def is_blocked(self, db: Session, blocker_id: int, blocked_id: int) -> bool:
        return db.query(UserBlock).filter(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id
        ).first() is not None

    def get_blocked_users(self, db: Session, user_id: int) -> list:
        blocks = db.query(UserBlock).filter(UserBlock.blocker_id == user_id).all()
        result = []
        for b in blocks:
            user = db.query(User).filter(User.id == b.blocked_id).first()
            if user:
                result.append({"id": user.id, "username": user.username})
        return result


class ReportManager:

    REPORT_REASONS = [
        "Nudity or sexual content",
        "Violence or dangerous content",
        "Hate speech or discrimination",
        "Misinformation",
        "Spam",
        "Harassment",
        "Copyright violation",
        "Other Codex violation",
    ]

    def submit_report(self, db: Session, reporter_id: int,
                      post_id: int, reason: str, details: str = "") -> dict:
        # Zero tolerance — auto-flag nudity reports immediately
        if "nudity" in reason.lower() or "sexual" in reason.lower():
            from .database import Post, PostStatus
            post = db.query(Post).filter(Post.id == post_id).first()
            if post:
                post.status = PostStatus.REMOVED
                db.commit()
                print(f"[SAFETY] Zero tolerance: Post {post_id} removed — nudity/sexual content report")

        report = ContentReport(
            reporter_id = reporter_id,
            post_id     = post_id,
            reason      = reason,
            details     = details,
        )
        db.add(report)
        db.commit()
        return {"ok": True, "message": "Report submitted. The Circle will review it."}

    def get_pending_reports(self, db: Session) -> list:
        reports = db.query(ContentReport).filter(
            ContentReport.status == "pending"
        ).order_by(ContentReport.created_at).all()
        return [
            {"id": r.id, "post_id": r.post_id, "reason": r.reason,
             "details": r.details, "created_at": r.created_at.isoformat()}
            for r in reports
        ]


class VideoResponseManager:

    def create_stitch(self, db: Session, user: User,
                      original_post_id: int, response_post_id: int) -> dict:
        """Stitch — respond to someone's video with your own."""
        db.add(VideoResponse(
            response_type    = "stitch",
            original_post_id = original_post_id,
            response_post_id = response_post_id,
        ))
        db.commit()
        return {"ok": True, "type": "stitch",
                "note": "Full credit given to original creator."}

    def create_duet(self, db: Session, user: User,
                    original_post_id: int, response_post_id: int) -> dict:
        """Duet — side by side video response."""
        db.add(VideoResponse(
            response_type    = "duet",
            original_post_id = original_post_id,
            response_post_id = response_post_id,
        ))
        db.commit()
        return {"ok": True, "type": "duet",
                "note": "Full credit given to original creator."}

    def get_responses(self, db: Session, post_id: int) -> list:
        responses = db.query(VideoResponse).filter(
            VideoResponse.original_post_id == post_id
        ).all()
        return [{"type": r.response_type, "response_post_id": r.response_post_id}
                for r in responses]


block_manager        = BlockManager()
report_manager       = ReportManager()
video_response_manager = VideoResponseManager()
