"""
preferences.py — The Commons Preference Engine

Learns what each user genuinely values.
Pointed at community value — not addiction.

What we track:
  - Watch time on videos (did they finish or scroll past?)
  - Topic engagement (what subjects do they interact with?)
  - Creator affinity (do they consistently engage with certain creators?)
  - Content type preference (video, text, image, audio)
  - Regional relevance (content from their area)

What we never do:
  - Build a hidden behavioral profile
  - Use psychological manipulation to extend session time
  - Hide what we know about you
  - Sell or share any of it
  - Optimize for outrage or anxiety

Everything is transparent. Everything is visible to the user.
Everything can be reset or deleted at any time.

Codex Law 5: Transparency.
Codex Law 3: No data selling.
Codex Law 1: People First.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

import json
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .database import Base, Post, User, PostStatus
from .config import config


# ── Preference Models ─────────────────────────────────────────────────────────

class UserTopicPreference(Base):
    """
    What topics does this user engage with?
    Transparent — user can see and reset this at any time.
    """
    __tablename__ = "user_topic_preferences"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic       = Column(String(100), nullable=False)
    score       = Column(Float, default=1.0)   # Higher = more interest shown
    updated_at  = Column(DateTime, default=datetime.utcnow)


class UserCreatorAffinity(Base):
    """
    Does this user consistently engage with certain creators?
    Transparent — user can see and reset this at any time.
    """
    __tablename__ = "user_creator_affinity"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator_id  = Column(Integer, ForeignKey("users.id"), nullable=False)
    score       = Column(Float, default=1.0)
    updated_at  = Column(DateTime, default=datetime.utcnow)


class UserContentTypePreference(Base):
    """
    Does this user prefer video, text, images, or audio?
    """
    __tablename__ = "user_content_type_preferences"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    content_type = Column(String(50), nullable=False)  # video, text, image, audio
    score        = Column(Float, default=1.0)
    updated_at   = Column(DateTime, default=datetime.utcnow)


class WatchEvent(Base):
    """
    Did the user finish a video or scroll past?
    Used to understand genuine interest vs passive exposure.
    Never used to maximize watch time — used to understand preference.
    """
    __tablename__ = "watch_events"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id         = Column(Integer, ForeignKey("posts.id"), nullable=False)
    watch_percent   = Column(Float, default=0.0)   # 0-100, how much they watched
    completed       = Column(Boolean, default=False)
    recorded_at     = Column(DateTime, default=datetime.utcnow)


# ── Topic Detection ───────────────────────────────────────────────────────────

TOPIC_KEYWORDS = {
    "music":        ["music", "song", "concert", "band", "album", "artist", "guitar", "piano", "rap", "hip hop"],
    "art":          ["art", "painting", "drawing", "sketch", "design", "creative", "illustration", "photography"],
    "cooking":      ["recipe", "cooking", "food", "bake", "chef", "meal", "kitchen", "ingredient", "eat"],
    "fitness":      ["workout", "fitness", "gym", "exercise", "health", "yoga", "running", "strength"],
    "news":         ["news", "breaking", "report", "update", "announcement", "latest", "today"],
    "politics":     ["election", "government", "policy", "vote", "congress", "president", "law", "rights"],
    "science":      ["science", "research", "study", "data", "discovery", "space", "climate", "biology"],
    "technology":   ["tech", "software", "app", "code", "AI", "computer", "phone", "internet", "digital"],
    "sports":       ["game", "team", "player", "score", "match", "league", "championship", "season"],
    "comedy":       ["funny", "humor", "laugh", "joke", "comedy", "meme", "hilarious"],
    "education":    ["learn", "teach", "school", "lesson", "tutorial", "how to", "explain", "understand"],
    "local":        ["community", "local", "neighborhood", "city", "town", "region", "nearby"],
    "business":     ["business", "startup", "entrepreneur", "market", "product", "launch", "company"],
    "nature":       ["nature", "outdoor", "wildlife", "environment", "garden", "animals", "hiking"],
    "dance":        ["dance", "dancing", "choreography", "moves", "dancer", "performance"],
    "fashion":      ["fashion", "style", "outfit", "clothing", "wear", "trend", "look"],
}


def detect_topics(text: str) -> List[str]:
    """Detect topics from post content."""
    if not text:
        return []
    text_lower = text.lower()
    detected = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            detected.append(topic)
    return detected


# ── Preference Engine ─────────────────────────────────────────────────────────

class PreferenceEngine:
    """
    Learns user preferences from engagement signals.
    Transparent, user-controlled, never manipulative.
    """

    # How much each signal type affects preference scores
    VOTE_WEIGHT        = 2.0   # Explicit vote — strongest signal
    COMPLETE_WEIGHT    = 1.5   # Finished watching — strong signal
    VIEW_WEIGHT        = 0.5   # Viewed — weak signal
    SKIP_WEIGHT        = -0.3  # Scrolled past quickly — mild negative
    DECAY_DAYS         = 30    # Preferences decay over 30 days if not reinforced

    def record_engagement(self, db: Session, user_id: int,
                          post: Post, engagement_type: str,
                          watch_percent: float = 0.0):
        """
        Record that a user engaged with a post.
        engagement_type: 'vote', 'view', 'complete', 'skip'
        """
        weight = {
            "vote":     self.VOTE_WEIGHT,
            "complete": self.COMPLETE_WEIGHT,
            "view":     self.VIEW_WEIGHT,
            "skip":     self.SKIP_WEIGHT,
        }.get(engagement_type, 0.0)

        if weight == 0:
            return

        # Detect topics from post content
        topics = detect_topics(post.content or "")

        # Update topic preferences
        for topic in topics:
            self._update_topic(db, user_id, topic, weight)

        # Update creator affinity
        if post.author_id and post.author_id != user_id:
            self._update_creator(db, user_id, post.author_id, weight)

        # Update content type preference
        if post.post_type:
            self._update_content_type(db, user_id, post.post_type.value, weight)

        # Record watch event for videos
        if post.post_type and post.post_type.value == "video" and watch_percent > 0:
            self._record_watch(db, user_id, post.id, watch_percent)

        db.commit()

    def get_personalized_feed(self, db: Session, user: User,
                               limit: int = 20, offset: int = 0) -> List[dict]:
        """
        Get personalized feed for this user.
        Scores each post based on their preference profile.
        Returns posts with explanation of why each was chosen.
        Transparent — user can see the reasoning.
        """
        # Get user's preference profile
        profile = self.get_profile(db, user.id)

        # Get candidate posts — published, not yet seen
        candidates = (
            db.query(Post)
            .filter(Post.status == PostStatus.PUBLISHED)
            .filter(Post.author_id != user.id)
            .order_by(Post.published_at.desc())
            .limit(200)   # Score from a pool of recent posts
            .all()
        )

        # Score each candidate
        scored = []
        for post in candidates:
            score, reason = self._score_post(post, profile, user)
            scored.append({
                "post":   post,
                "score":  score,
                "reason": reason,
            })

        # Sort by score
        scored.sort(key=lambda x: x["score"], reverse=True)

        # Apply youth filter
        if user.is_minor:
            scored = [s for s in scored if not s["post"].is_political]

        return scored[offset:offset + limit]

    def _score_post(self, post: Post, profile: dict, user: User) -> tuple:
        """
        Score a post for this user. Returns (score, reason).
        Completely transparent — reason explains the score.
        """
        score  = 0.0
        reason = None

        # Topic match
        topics = detect_topics(post.content or "")
        topic_scores = profile.get("topics", {})
        matched_topics = []
        for topic in topics:
            if topic in topic_scores and topic_scores[topic] > 1.0:
                score += topic_scores[topic] * 0.4
                matched_topics.append(topic)

        # Creator affinity
        creator_scores = profile.get("creators", {})
        if str(post.author_id) in creator_scores:
            creator_boost = creator_scores[str(post.author_id)]
            if creator_boost > 1.0:
                score += creator_boost * 0.3
                reason = f"Shown because: you consistently engage with this creator"

        # Content type preference
        type_scores = profile.get("content_types", {})
        post_type = post.post_type.value if post.post_type else "text"
        if post_type in type_scores and type_scores[post_type] > 1.0:
            score += type_scores[post_type] * 0.2

        # Community value — high community score boosts all users
        score += post.community_score * 0.1

        # Recency boost — newer content gets a small boost
        if post.published_at:
            age_hours = (datetime.utcnow() - post.published_at).total_seconds() / 3600
            if age_hours < 24:
                score += max(0, (24 - age_hours) / 24) * 0.2

        # Build transparent reason
        if not reason:
            if matched_topics:
                reason = f"Shown because: matches your interest in {', '.join(matched_topics[:2])}"
            elif post.community_score > 5:
                reason = "Shown because: highly valued by the community"
            elif post.published_at and (datetime.utcnow() - post.published_at).total_seconds() < 3600:
                reason = "Shown because: posted recently"
            else:
                reason = "Shown because: active content on The Commons"

        return score, reason

    # ── Profile Management ────────────────────────────────────────────────────

    def get_profile(self, db: Session, user_id: int) -> dict:
        """
        Get a user's full preference profile.
        Transparent — this is what the user sees when they check their preferences.
        """
        topics = {
            p.topic: p.score
            for p in db.query(UserTopicPreference)
            .filter(UserTopicPreference.user_id == user_id)
            .all()
        }
        creators = {
            str(p.creator_id): p.score
            for p in db.query(UserCreatorAffinity)
            .filter(UserCreatorAffinity.user_id == user_id)
            .all()
        }
        content_types = {
            p.content_type: p.score
            for p in db.query(UserContentTypePreference)
            .filter(UserContentTypePreference.user_id == user_id)
            .all()
        }
        return {
            "topics":        topics,
            "creators":      creators,
            "content_types": content_types,
        }

    def reset_preferences(self, db: Session, user_id: int) -> dict:
        """
        User resets their preference profile completely.
        Codex Law 3 — users control their own data.
        """
        db.query(UserTopicPreference).filter(
            UserTopicPreference.user_id == user_id
        ).delete()
        db.query(UserCreatorAffinity).filter(
            UserCreatorAffinity.user_id == user_id
        ).delete()
        db.query(UserContentTypePreference).filter(
            UserContentTypePreference.user_id == user_id
        ).delete()
        db.query(WatchEvent).filter(
            WatchEvent.user_id == user_id
        ).delete()
        db.commit()
        print(f"[PREFERENCES] User {user_id} reset their preference profile.")
        return {"ok": True, "message": "Your preference profile has been reset."}

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _update_topic(self, db: Session, user_id: int,
                      topic: str, weight: float):
        existing = (
            db.query(UserTopicPreference)
            .filter(UserTopicPreference.user_id == user_id,
                    UserTopicPreference.topic == topic)
            .first()
        )
        if existing:
            existing.score     = max(0.1, existing.score + weight)
            existing.updated_at = datetime.utcnow()
        else:
            db.add(UserTopicPreference(
                user_id    = user_id,
                topic      = topic,
                score      = max(0.1, 1.0 + weight),
            ))

    def _update_creator(self, db: Session, user_id: int,
                        creator_id: int, weight: float):
        existing = (
            db.query(UserCreatorAffinity)
            .filter(UserCreatorAffinity.user_id == user_id,
                    UserCreatorAffinity.creator_id == creator_id)
            .first()
        )
        if existing:
            existing.score      = max(0.1, existing.score + weight)
            existing.updated_at = datetime.utcnow()
        else:
            db.add(UserCreatorAffinity(
                user_id    = user_id,
                creator_id = creator_id,
                score      = max(0.1, 1.0 + weight),
            ))

    def _update_content_type(self, db: Session, user_id: int,
                             content_type: str, weight: float):
        existing = (
            db.query(UserContentTypePreference)
            .filter(UserContentTypePreference.user_id == user_id,
                    UserContentTypePreference.content_type == content_type)
            .first()
        )
        if existing:
            existing.score      = max(0.1, existing.score + weight)
            existing.updated_at = datetime.utcnow()
        else:
            db.add(UserContentTypePreference(
                user_id      = user_id,
                content_type = content_type,
                score        = max(0.1, 1.0 + weight),
            ))

    def _record_watch(self, db: Session, user_id: int,
                      post_id: int, watch_percent: float):
        db.add(WatchEvent(
            user_id       = user_id,
            post_id       = post_id,
            watch_percent = watch_percent,
            completed     = watch_percent >= 90,
        ))


preference_engine = PreferenceEngine()
