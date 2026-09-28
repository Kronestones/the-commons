"""
account_safety.py — Direct-message safety scanning & account restriction

Purpose: detect patterns associated with predatory contact toward minors
in direct messages, and gate access while a human moderator reviews —
never fully automated removal.

Flow:
  1. commons/dm_safety.py scores an outgoing DM for risk signals.
  2. If any signals fire, the SENDING account is immediately restricted
     platform-wide: messaging is paused, browsing still works, and the
     only messaging still possible is to Sovereign/team support for
     review — that goes through commons/team_messaging.py, a separate
     system this module never touches.
  3. A Sovereign reviews the flag: dismiss (false positive — restriction
     lifted immediately) or confirm (restriction stands; the account
     has 14 days from when it was first restricted to reach out and
     resolve it before being soft-deactivated and its email banned from
     re-registering).
  4. A background sweep (same pattern as commons/maintenance.py) checks
     hourly for restrictions past their 14-day window and finalizes
     removal automatically if nobody acted on it.

Honesty note: this module reads DirectMessage content server-side to
run the scan above. commons/features.py's DirectMessage/
DirectMessageManager docstrings previously claimed messages are
end-to-end encrypted and unreadable by the platform — that was already
inaccurate before this change (content_encrypted was stored as plain
text, per the existing TODO), and is now actively untrue given this
scan. Those docstrings are updated as part of this same patch. Any
public-facing disclosure/Codex language claiming DMs are unmonitored
needs updating too.
"""

import threading
import time
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Session

from .database import Base, User, SessionLocal

RESTRICTION_WINDOW_DAYS = 14
SWEEP_INTERVAL_HOURS = 1


class AccountRestriction(Base):
    """One row per account that has ever been restricted. Reused across
    repeated flags on the same account — a second flag while already
    restricted does not reset the 14-day clock."""
    __tablename__ = "account_restrictions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    reason        = Column(Text, nullable=False)          # comma-joined signal names
    status        = Column(String(20), default="active")  # active | lifted | expired_removed
    restricted_at = Column(DateTime, default=datetime.utcnow)
    expires_at    = Column(DateTime, nullable=False)
    resolved_at   = Column(DateTime, nullable=True)


class MessageFlag(Base):
    """One row per flagged message — the evidence trail behind a
    restriction, shown to Sovereign in the moderation queue."""
    __tablename__ = "message_flags"

    id           = Column(Integer, primary_key=True, index=True)
    message_id   = Column(Integer, ForeignKey("direct_messages.id"), nullable=False)
    sender_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    signals      = Column(Text, nullable=False)           # comma-joined signal names
    status       = Column(String(20), default="pending")  # pending | confirmed | dismissed
    created_at   = Column(DateTime, default=datetime.utcnow)
    reviewed_at  = Column(DateTime, nullable=True)


class BannedEmail(Base):
    """Emails permanently blocked from re-registering, set when a
    restricted account's 14-day window expires unresolved."""
    __tablename__ = "banned_emails"

    id        = Column(Integer, primary_key=True, index=True)
    email     = Column(String(255), unique=True, nullable=False)
    reason    = Column(Text, default="")
    banned_at = Column(DateTime, default=datetime.utcnow)


class AccountSafetyManager:

    def is_restricted(self, db: Session, user_id: int) -> bool:
        r = db.query(AccountRestriction).filter(
            AccountRestriction.user_id == user_id,
            AccountRestriction.status == "active",
        ).first()
        return r is not None

    def restrict_account(self, db: Session, user_id: int, signals: list) -> None:
        existing = db.query(AccountRestriction).filter(
            AccountRestriction.user_id == user_id,
            AccountRestriction.status == "active",
        ).first()
        if existing:
            # Already restricted and the clock is already running — don't
            # reset it. The MessageFlag row created alongside this call
            # already records the additional signals separately.
            return
        now = datetime.utcnow()
        restriction = AccountRestriction(
            user_id       = user_id,
            reason        = ",".join(signals),
            status        = "active",
            restricted_at = now,
            expires_at    = now + timedelta(days=RESTRICTION_WINDOW_DAYS),
        )
        db.add(restriction)
        db.commit()

    def flag_message(self, db: Session, msg, sender: User, recipient: User, signals: list) -> None:
        flag = MessageFlag(
            message_id   = msg.id,
            sender_id    = sender.id,
            recipient_id = recipient.id,
            signals      = ",".join(signals),
            status       = "pending",
        )
        db.add(flag)
        db.commit()
        self.restrict_account(db, sender.id, signals)

    def get_pending_flags(self, db: Session) -> list:
        flags = db.query(MessageFlag).filter(
            MessageFlag.status == "pending"
        ).order_by(MessageFlag.created_at.desc()).all()

        result = []
        for f in flags:
            sender = db.query(User).filter(User.id == f.sender_id).first()
            recipient = db.query(User).filter(User.id == f.recipient_id).first()
            result.append({
                "id":         f.id,
                "sender":     sender.username if sender else "unknown",
                "recipient":  recipient.username if recipient else "unknown",
                "signals":    f.signals.split(","),
                "created_at": f.created_at.isoformat(),
            })
        return result

    def confirm_flag(self, db: Session, flag_id: int) -> dict:
        flag = db.query(MessageFlag).filter(MessageFlag.id == flag_id).first()
        if not flag:
            return {"ok": False, "error": "Flag not found."}
        flag.status = "confirmed"
        flag.reviewed_at = datetime.utcnow()
        db.commit()
        return {"ok": True}

    def dismiss_flag(self, db: Session, flag_id: int) -> dict:
        flag = db.query(MessageFlag).filter(MessageFlag.id == flag_id).first()
        if not flag:
            return {"ok": False, "error": "Flag not found."}
        flag.status = "dismissed"
        flag.reviewed_at = datetime.utcnow()
        db.commit()
        self.lift_restriction(db, flag.sender_id)
        return {"ok": True}

    def lift_restriction(self, db: Session, user_id: int) -> None:
        r = db.query(AccountRestriction).filter(
            AccountRestriction.user_id == user_id,
            AccountRestriction.status == "active",
        ).first()
        if r:
            r.status = "lifted"
            r.resolved_at = datetime.utcnow()
            db.commit()

    def finalize_expired(self, db: Session) -> int:
        """Soft-deactivate + ban the email for every restriction whose
        14-day window has passed with no resolution. Returns the count
        finalized."""
        now = datetime.utcnow()
        expired = db.query(AccountRestriction).filter(
            AccountRestriction.status == "active",
            AccountRestriction.expires_at <= now,
        ).all()
        count = 0
        for r in expired:
            user = db.query(User).filter(User.id == r.user_id).first()
            if user:
                user.is_active = False
                if not db.query(BannedEmail).filter(BannedEmail.email == user.email).first():
                    db.add(BannedEmail(email=user.email, reason="Unresolved account restriction expired."))
            r.status = "expired_removed"
            r.resolved_at = now
            count += 1
        if expired:
            db.commit()
        return count


class RestrictionScheduler:
    """Background sweep for expired restrictions — mirrors the pattern
    already used by commons/maintenance.py's MaintenanceManager."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._scheduler, daemon=True)
        self._thread.start()
        print("[ACCOUNT_SAFETY] Restriction expiry scheduler started.")

    def stop(self):
        self._stop_event.set()

    def _scheduler(self):
        while not self._stop_event.is_set():
            try:
                db = SessionLocal()
                try:
                    count = account_safety_manager.finalize_expired(db)
                    if count:
                        print(f"[ACCOUNT_SAFETY] Finalized {count} expired restriction(s).")
                finally:
                    db.close()
            except Exception as e:
                print(f"[ACCOUNT_SAFETY] Sweep error: {e}")
            time.sleep(SWEEP_INTERVAL_HOURS * 3600)


account_safety_manager = AccountSafetyManager()
restriction_scheduler = RestrictionScheduler()
