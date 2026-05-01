"""
livestream.py — The Commons Live Streaming & Real-Time Chat

Live video broadcasting with real-time community chat.
Gifts during streams. Viewer counts. Stream management.

Built on WebSockets for real-time connection.
Requires additional infrastructure to go fully live —
currently in development, coming soon to The Commons.

What this module provides:
  - Stream session management (start/end/pause)
  - Real-time chat messages during streams
  - Live viewer count tracking
  - Gift events during streams (connected to payments.py)
  - Stream recording metadata
  - Replay availability after stream ends

What requires additional infrastructure:
  - WebSocket server (FastAPI WebSockets or separate service)
  - Video ingestion (RTMP server — nginx-rtmp or similar)
  - CDN for video distribution
  - These will be added when operational capacity allows

Transparency to users:
  - Live streaming is coming to The Commons
  - The framework is built and ready
  - Infrastructure deployment is the next step
  - Community will be notified when live goes live

Codex Law 1: People First — be honest about what's ready.
Codex Law 5: Transparency — no fake features.

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Session
from .database import Base, User


# ── Stream Status ─────────────────────────────────────────────────────────────

class StreamStatus:
    SCHEDULED  = "scheduled"
    LIVE       = "live"
    PAUSED     = "paused"
    ENDED      = "ended"
    REPLAY     = "replay"


# ── Models ────────────────────────────────────────────────────────────────────

class LiveStream(Base):
    """
    A live stream session.
    Created when a user goes live.
    """
    __tablename__ = "live_streams"

    id              = Column(Integer, primary_key=True, index=True)
    streamer_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    title           = Column(String(300), nullable=False)
    description     = Column(Text, default="")
    category        = Column(String(100), default="general")
    status          = Column(String(50), default=StreamStatus.SCHEDULED)
    viewer_count    = Column(Integer, default=0)
    peak_viewers    = Column(Integer, default=0)
    total_gifts     = Column(Float, default=0.0)
    chat_enabled    = Column(Boolean, default=True)
    gifts_enabled   = Column(Boolean, default=True)
    is_recorded     = Column(Boolean, default=False)
    replay_available = Column(Boolean, default=False)
    stream_key      = Column(String(255), default="")  # For RTMP ingestion
    scheduled_for   = Column(DateTime, nullable=True)
    started_at      = Column(DateTime, nullable=True)
    ended_at        = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)


class LiveChatMessage(Base):
    """
    Real-time chat message during a live stream.
    Stored for replay and moderation.
    """
    __tablename__ = "live_chat_messages"

    id          = Column(Integer, primary_key=True, index=True)
    stream_id   = Column(Integer, ForeignKey("live_streams.id"), nullable=False)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    message     = Column(Text, nullable=False)
    is_removed  = Column(Boolean, default=False)
    is_pinned   = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


class StreamViewer(Base):
    """Tracks who is watching a stream."""
    __tablename__ = "stream_viewers"

    id          = Column(Integer, primary_key=True, index=True)
    stream_id   = Column(Integer, ForeignKey("live_streams.id"), nullable=False)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    joined_at   = Column(DateTime, default=datetime.utcnow)
    left_at     = Column(DateTime, nullable=True)
    is_active   = Column(Boolean, default=True)


class StreamGiftEvent(Base):
    """
    Gift sent during a live stream.
    Connected to payments.py for actual processing.
    """
    __tablename__ = "stream_gift_events"

    id          = Column(Integer, primary_key=True, index=True)
    stream_id   = Column(Integer, ForeignKey("live_streams.id"), nullable=False)
    sender_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    gift_type   = Column(String(50), nullable=False)
    gift_emoji  = Column(String(10), default="❤️")
    usd_value   = Column(Float, nullable=False)
    message     = Column(String(200), default="")
    created_at  = Column(DateTime, default=datetime.utcnow)


# ── Stream Manager ────────────────────────────────────────────────────────────

class LiveStreamManager:

    def create_stream(self, db: Session, streamer: User,
                      title: str, description: str = "",
                      category: str = "general",
                      scheduled_for: Optional[datetime] = None,
                      chat_enabled: bool = True,
                      gifts_enabled: bool = True) -> dict:
        """Create a new stream session."""
        import secrets

        if not title or len(title.strip()) == 0:
            return {"ok": False, "error": "Stream title required."}
        if len(title) > 300:
            return {"ok": False, "error": "Title too long."}

        # Generate stream key for RTMP ingestion
        stream_key = secrets.token_urlsafe(32)

        stream = LiveStream(
            streamer_id   = streamer.id,
            title         = title.strip(),
            description   = description,
            category      = category,
            status        = StreamStatus.SCHEDULED if scheduled_for else StreamStatus.SCHEDULED,
            stream_key    = stream_key,
            scheduled_for = scheduled_for,
            chat_enabled  = chat_enabled,
            gifts_enabled = gifts_enabled,
        )
        db.add(stream)
        db.commit()
        db.refresh(stream)

        return {
            "ok":         True,
            "stream_id":  stream.id,
            "stream_key": stream_key,
            "status":     stream.status,
            "message":    "Stream created. Go live when ready.",
            "coming_soon_note": (
                "Full live streaming infrastructure is coming to The Commons. "
                "Stream sessions and chat are ready — video broadcasting "
                "infrastructure is being deployed. Thank you for your patience."
            )
        }

    def go_live(self, db: Session, stream_id: int, streamer: User) -> dict:
        """Start a stream — go live."""
        stream = db.query(LiveStream).filter(
            LiveStream.id         == stream_id,
            LiveStream.streamer_id == streamer.id
        ).first()
        if not stream:
            return {"ok": False, "error": "Stream not found."}
        if stream.status == StreamStatus.LIVE:
            return {"ok": False, "error": "Already live."}

        stream.status     = StreamStatus.LIVE
        stream.started_at = datetime.utcnow()
        db.commit()

        return {
            "ok":      True,
            "status":  StreamStatus.LIVE,
            "message": "You are live! Welcome your viewers. 🎉"
        }

    def end_stream(self, db: Session, stream_id: int,
                   streamer: User, make_replay: bool = True) -> dict:
        """End a live stream."""
        stream = db.query(LiveStream).filter(
            LiveStream.id          == stream_id,
            LiveStream.streamer_id == streamer.id
        ).first()
        if not stream:
            return {"ok": False, "error": "Stream not found."}

        stream.status           = StreamStatus.ENDED
        stream.ended_at         = datetime.utcnow()
        stream.replay_available = make_replay

        # Final viewer count
        active_viewers = db.query(StreamViewer).filter(
            StreamViewer.stream_id == stream_id,
            StreamViewer.is_active == True
        ).all()
        for v in active_viewers:
            v.is_active = False
            v.left_at   = datetime.utcnow()

        db.commit()

        duration = None
        if stream.started_at:
            duration = int((datetime.utcnow() - stream.started_at).total_seconds() / 60)

        return {
            "ok":           True,
            "status":       StreamStatus.ENDED,
            "duration_min": duration,
            "peak_viewers": stream.peak_viewers,
            "total_gifts":  f"${stream.total_gifts:.2f}",
            "replay":       make_replay,
            "message":      "Stream ended. Thank you for going live on The Commons."
        }

    def send_chat(self, db: Session, stream_id: int,
                  user: User, message: str) -> dict:
        """Send a chat message during a live stream."""
        # Zero tolerance content check
        from .fingerprint import check_zero_tolerance
        if check_zero_tolerance(message):
            return {"ok": False, "error": "Message contains content not permitted on The Commons."}

        if not message or len(message.strip()) == 0:
            return {"ok": False, "error": "Message cannot be empty."}
        if len(message) > 500:
            return {"ok": False, "error": "Message too long. Maximum 500 characters."}

        stream = db.query(LiveStream).filter(
            LiveStream.id     == stream_id,
            LiveStream.status == StreamStatus.LIVE
        ).first()
        if not stream:
            return {"ok": False, "error": "Stream is not live."}
        if not stream.chat_enabled:
            return {"ok": False, "error": "Chat is disabled for this stream."}

        chat = LiveChatMessage(
            stream_id = stream_id,
            user_id   = user.id,
            message   = message.strip(),
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

        return {
            "ok":         True,
            "message_id": chat.id,
            "username":   user.username,
            "message":    message.strip(),
            "sent_at":    chat.created_at.isoformat(),
        }

    def get_chat(self, db: Session, stream_id: int,
                 limit: int = 50, since_id: int = 0) -> List[dict]:
        """Get recent chat messages for a stream."""
        query = db.query(LiveChatMessage).filter(
            LiveChatMessage.stream_id  == stream_id,
            LiveChatMessage.is_removed == False,
        )
        if since_id:
            query = query.filter(LiveChatMessage.id > since_id)

        messages = query.order_by(LiveChatMessage.created_at.desc()).limit(limit).all()

        result = []
        for m in reversed(messages):
            user = db.query(User).filter(User.id == m.user_id).first()
            result.append({
                "id":        m.id,
                "username":  user.username if user else "unknown",
                "message":   m.message,
                "is_pinned": m.is_pinned,
                "sent_at":   m.created_at.isoformat(),
            })
        return result

    def join_stream(self, db: Session, stream_id: int,
                    user_id: Optional[int] = None) -> dict:
        """Record a viewer joining."""
        stream = db.query(LiveStream).filter(
            LiveStream.id     == stream_id,
            LiveStream.status == StreamStatus.LIVE
        ).first()
        if not stream:
            return {"ok": False, "error": "Stream not found or not live."}

        viewer = StreamViewer(
            stream_id = stream_id,
            user_id   = user_id,
        )
        db.add(viewer)

        # Update viewer count
        active = db.query(StreamViewer).filter(
            StreamViewer.stream_id == stream_id,
            StreamViewer.is_active == True
        ).count()
        stream.viewer_count = active + 1
        if stream.viewer_count > stream.peak_viewers:
            stream.peak_viewers = stream.viewer_count

        db.commit()

        return {
            "ok":           True,
            "viewer_count": stream.viewer_count,
            "title":        stream.title,
            "streamer_id":  stream.streamer_id,
            "chat_enabled": stream.chat_enabled,
            "gifts_enabled": stream.gifts_enabled,
        }

    def leave_stream(self, db: Session, stream_id: int,
                     user_id: Optional[int] = None) -> dict:
        """Record a viewer leaving."""
        viewer = db.query(StreamViewer).filter(
            StreamViewer.stream_id == stream_id,
            StreamViewer.user_id   == user_id,
            StreamViewer.is_active == True
        ).first()
        if viewer:
            viewer.is_active = False
            viewer.left_at   = datetime.utcnow()

            stream = db.query(LiveStream).filter(LiveStream.id == stream_id).first()
            if stream and stream.viewer_count > 0:
                stream.viewer_count -= 1
            db.commit()

        return {"ok": True}

    def get_active_streams(self, db: Session,
                           limit: int = 20) -> List[dict]:
        """Get all currently live streams."""
        streams = db.query(LiveStream).filter(
            LiveStream.status == StreamStatus.LIVE
        ).order_by(LiveStream.viewer_count.desc()).limit(limit).all()

        result = []
        for s in streams:
            streamer = db.query(User).filter(User.id == s.streamer_id).first()
            result.append({
                "id":           s.id,
                "title":        s.title,
                "category":     s.category,
                "streamer":     streamer.username if streamer else "unknown",
                "viewer_count": s.viewer_count,
                "total_gifts":  f"${s.total_gifts:.2f}",
                "started_at":   s.started_at.isoformat() if s.started_at else None,
                "gifts_enabled": s.gifts_enabled,
            })
        return result

    def get_stream_info(self, db: Session, stream_id: int) -> Optional[dict]:
        """Get full info about a stream."""
        stream = db.query(LiveStream).filter(LiveStream.id == stream_id).first()
        if not stream:
            return None

        streamer = db.query(User).filter(User.id == stream.streamer_id).first()
        return {
            "id":              stream.id,
            "title":           stream.title,
            "description":     stream.description,
            "category":        stream.category,
            "status":          stream.status,
            "streamer":        streamer.username if streamer else "unknown",
            "viewer_count":    stream.viewer_count,
            "peak_viewers":    stream.peak_viewers,
            "total_gifts":     f"${stream.total_gifts:.2f}",
            "chat_enabled":    stream.chat_enabled,
            "gifts_enabled":   stream.gifts_enabled,
            "replay_available": stream.replay_available,
            "started_at":      stream.started_at.isoformat() if stream.started_at else None,
            "ended_at":        stream.ended_at.isoformat() if stream.ended_at else None,
        }

    def remove_chat_message(self, db: Session, message_id: int,
                             requester: User) -> dict:
        """Remove a chat message — streamer or Circle can remove."""
        msg = db.query(LiveChatMessage).filter(
            LiveChatMessage.id == message_id
        ).first()
        if not msg:
            return {"ok": False, "error": "Message not found."}

        stream = db.query(LiveStream).filter(
            LiveStream.id == msg.stream_id
        ).first()

        if (stream and stream.streamer_id != requester.id and
                requester.role.value not in ("circle", "sovereign")):
            return {"ok": False, "error": "You cannot remove this message."}

        msg.is_removed = True
        db.commit()
        return {"ok": True}

    def pin_chat_message(self, db: Session, message_id: int,
                          streamer: User) -> dict:
        """Pin a chat message — streamer only."""
        msg = db.query(LiveChatMessage).filter(
            LiveChatMessage.id == message_id
        ).first()
        if not msg:
            return {"ok": False, "error": "Message not found."}

        stream = db.query(LiveStream).filter(
            LiveStream.id          == msg.stream_id,
            LiveStream.streamer_id == streamer.id
        ).first()
        if not stream:
            return {"ok": False, "error": "Only the streamer can pin messages."}

        # Unpin all others first
        db.query(LiveChatMessage).filter(
            LiveChatMessage.stream_id == msg.stream_id
        ).update({"is_pinned": False})

        msg.is_pinned = True
        db.commit()
        return {"ok": True, "message": "Message pinned."}


livestream_manager = LiveStreamManager()

# ── Coming Soon Notice ────────────────────────────────────────────────────────

COMING_SOON = {
    "feature":     "Live Streaming",
    "status":      "In Development",
    "what_works":  [
        "Stream session creation and management",
        "Live chat messages",
        "Viewer tracking",
        "Gift system framework",
        "Stream scheduling",
        "Replay metadata",
    ],
    "what_is_coming": [
        "Video broadcasting infrastructure (RTMP ingestion)",
        "CDN for global video distribution",
        "WebSocket real-time chat delivery",
        "Mobile streaming from The Commons app",
    ],
    "eta":  "Coming to The Commons — infrastructure being deployed",
    "note": "We are building this right. It will be worth the wait. Power to the People."
}
