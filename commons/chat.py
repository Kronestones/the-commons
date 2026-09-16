"""
commons/chat.py — The Commons public chat room

Adapted from the original chat feature design to match this codebase's
actual conventions: managers take User objects (not raw usernames),
matching commons/posts.py's PostManager.create(db, author, ...) style;
models live in commons/database.py, not a separate models.py; fields
use author_id/reporter_id/etc. (ForeignKey to users.id) instead of
plain username strings, so a username change doesn't orphan old
messages from the person who sent them.

Drop this file at: commons/chat.py
"""

import html
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from commons.database import ChatMessage, ChatReport, ChatBlock, ChatMessageStatus, User

# --- Tunable constants -------------------------------------------------

MAX_MESSAGE_LENGTH = 500
HISTORY_RETENTION_HOURS = 48       # messages older than this are purged
REPORT_THRESHOLD = 3               # unique reporters needed to auto-hide


class ChatManager:

    # --- Sending -----------------------------------------------------

    def send_message(self, db: Session, author: User, raw_message: str,
                      reply_to_id: Optional[int] = None) -> dict:
        message = raw_message.strip()
        if not message:
            return {"ok": False, "error": "Message cannot be empty."}
        if len(message) > MAX_MESSAGE_LENGTH:
            return {"ok": False, "error": f"Message too long (max {MAX_MESSAGE_LENGTH} characters)."}

        if reply_to_id is not None:
            target = db.query(ChatMessage).filter(ChatMessage.id == reply_to_id).first()
            if not target or target.status != ChatMessageStatus.VISIBLE:
                reply_to_id = None  # silently drop a reply to a missing/hidden message

        safe_message = html.escape(message)

        chat_message = ChatMessage(
            author_id   = author.id,
            content     = safe_message,
            status      = ChatMessageStatus.VISIBLE,
            reply_to_id = reply_to_id,
        )
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        return {"ok": True, "message": chat_message}

    # --- Reading -------------------------------------------------------

    def get_recent_messages(self, db: Session, viewer: Optional[User] = None,
                             limit: int = 200) -> List[dict]:
        self._purge_old_messages(db)

        cutoff = datetime.utcnow() - timedelta(hours=HISTORY_RETENTION_HOURS)

        blocked_ids = set()
        if viewer:
            blocked_ids = self._get_blocked_ids(db, viewer.id)

        query = (
            db.query(ChatMessage)
            .filter(ChatMessage.created_at >= cutoff)
            .filter(ChatMessage.status == ChatMessageStatus.VISIBLE)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )

        messages = query.all()

        if blocked_ids:
            messages = [m for m in messages if m.author_id not in blocked_ids]

        return [
            {
                "id":         m.id,
                "author":     m.author.username if m.author else "unknown",
                "author_id":  m.author_id,
                "content":    m.content,
                "created_at": m.created_at.isoformat(),
                "reply_to_id": m.reply_to_id,
                "reply_to_author": (m.reply_to.author.username if m.reply_to and m.reply_to.author else None),
                "reply_to_content": (m.reply_to.content if m.reply_to else None),
            }
            for m in messages
        ]

    def _purge_old_messages(self, db: Session):
        cutoff = datetime.utcnow() - timedelta(hours=HISTORY_RETENTION_HOURS)
        db.query(ChatMessage).filter(ChatMessage.created_at < cutoff).delete()
        db.commit()

    # --- Reporting -----------------------------------------------------

    def report_message(self, db: Session, message_id: int, reporter: User,
                        reason: Optional[str] = None) -> dict:
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            return {"ok": False, "error": "Message not found."}
        if message.author_id == reporter.id:
            return {"ok": False, "error": "You cannot report your own message."}

        existing = (
            db.query(ChatReport)
            .filter(
                ChatReport.message_id == message_id,
                ChatReport.reporter_id == reporter.id,
            )
            .first()
        )
        if existing:
            return {"ok": True, "status": "already_reported"}

        report = ChatReport(
            message_id  = message_id,
            reporter_id = reporter.id,
            reported_id = message.author_id,
            reason      = reason,
        )
        db.add(report)
        db.commit()

        unique_reporters = (
            db.query(func.count(func.distinct(ChatReport.reporter_id)))
            .filter(ChatReport.message_id == message_id)
            .scalar()
        )

        auto_hidden = False
        if unique_reporters >= REPORT_THRESHOLD and message.status == ChatMessageStatus.VISIBLE:
            message.status = ChatMessageStatus.HIDDEN_PENDING_REVIEW
            db.commit()
            auto_hidden = True

        return {"ok": True, "status": "reported", "auto_hidden": auto_hidden, "report_count": unique_reporters}

    def get_pending_review(self, db: Session) -> List[dict]:
        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.status == ChatMessageStatus.HIDDEN_PENDING_REVIEW)
            .order_by(ChatMessage.created_at.desc())
            .all()
        )
        result = []
        for m in messages:
            reports = db.query(ChatReport).filter(ChatReport.message_id == m.id).all()
            result.append({
                "id":           m.id,
                "author":       m.author.username if m.author else "unknown",
                "content":      m.content,
                "created_at":   m.created_at.isoformat(),
                "report_count": len(reports),
                "reasons":      [r.reason for r in reports if r.reason],
            })
        return result

    def confirm_removal(self, db: Session, message_id: int) -> dict:
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            return {"ok": False, "error": "Message not found."}
        message.status = ChatMessageStatus.REMOVED
        db.commit()
        return {"ok": True}

    def restore_message(self, db: Session, message_id: int) -> dict:
        message = db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        if not message:
            return {"ok": False, "error": "Message not found."}
        message.status = ChatMessageStatus.VISIBLE
        db.query(ChatReport).filter(ChatReport.message_id == message_id).delete()
        db.commit()
        return {"ok": True}

    # --- Blocking --------------------------------------------------------

    def block_user(self, db: Session, blocker: User, blocked_id: int) -> dict:
        if blocker.id == blocked_id:
            return {"ok": False, "error": "You cannot block yourself."}

        existing = (
            db.query(ChatBlock)
            .filter(
                ChatBlock.blocker_id == blocker.id,
                ChatBlock.blocked_id == blocked_id,
            )
            .first()
        )
        if existing:
            return {"ok": True, "status": "already_blocked"}

        block = ChatBlock(blocker_id=blocker.id, blocked_id=blocked_id)
        db.add(block)
        db.commit()
        return {"ok": True}

    def unblock_user(self, db: Session, blocker: User, blocked_id: int) -> dict:
        db.query(ChatBlock).filter(
            ChatBlock.blocker_id == blocker.id,
            ChatBlock.blocked_id == blocked_id,
        ).delete()
        db.commit()
        return {"ok": True}

    def _get_blocked_ids(self, db: Session, blocker_id: int) -> set:
        rows = (
            db.query(ChatBlock.blocked_id)
            .filter(ChatBlock.blocker_id == blocker_id)
            .all()
        )
        return {r[0] for r in rows}


chat_manager = ChatManager()
