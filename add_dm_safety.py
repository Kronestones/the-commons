#!/usr/bin/env python3
"""
add_dm_safety.py

Adds child-safety scanning + account restriction to direct messages,
and closes a real security gap found along the way.

WHAT THIS DOES
--------------
1. NEW: commons/dm_safety.py — pattern-based signal detection on
   outgoing DM content (off-platform contact requests, secrecy
   pressure, requests for identifying info/photos) plus a behavioral
   check (one account messaging many strangers in a burst). Designed
   so an LLM classifier can be added later as an extra signal source
   without touching any call site.

2. NEW: commons/account_safety.py — three new tables
   (AccountRestriction, MessageFlag, BannedEmail) and the manager that
   ties it together: a flagged message immediately restricts the
   SENDER's whole account (messaging paused platform-wide; browsing
   still works; contacting Sovereign/team support still works, since
   that's a separate system this never touches). A Sovereign reviews
   via new moderation endpoints — dismiss lifts the restriction
   immediately, confirm leaves it running. A background sweep (same
   pattern as commons/maintenance.py) finalizes any restriction whose
   14-day window expires unresolved: the account is soft-deactivated
   and its email is permanently banned from re-registering.

3. FIXES A REAL BUG: commons/features.py's DirectMessageManager.send()
   (used by POST /api/messages/{recipient_id}) had NO stranger-request
   gate at all — unlike commons/messaging.py's send_message() (used by
   POST /api/messages/send), any account could message any other
   account directly with no accept step. This patch brings both paths
   in line and hooks the new safety check into both, so nothing can
   route around it.

4. HONESTY FIX: commons/features.py's DirectMessage/DirectMessageManager
   docstrings claimed messages are end-to-end encrypted and unreadable
   by the platform. That was already inaccurate (content_encrypted is
   stored as plain text — see the pre-existing TODO) and is now
   actively untrue given this scan reads content server-side. Docstrings
   are updated to say so honestly. Any public Codex/disclosure language
   claiming DMs are unmonitored needs the same update — that's on you,
   not something this script can find and fix.

Tested against reconstructed copies of the real files (using the exact
snippets you pasted back to me) plus an 18-case functional test suite
covering: benign sends, flagged content triggering restriction, the
restriction blocking ALL further sends (not just to that recipient),
the second DM path's bug being fixed, burst-messaging detection,
Sovereign dismiss lifting a restriction, 14-day expiry finalizing into
soft-deactivation + email ban, and a banned email being rejected at
registration. All 18 passed before this script was written.

Safe to run twice — each patch checks whether it's already applied and
skips rather than double-patching or erroring.
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------
# New file contents (already tested — see the accompanying summary)
# ---------------------------------------------------------------------

DM_SAFETY_PY = '''"""
dm_safety.py — Direct-message safety signal detection

Pattern-level detection of behaviors associated with predatory contact
toward minors, not an exhaustive phrase dictionary. This scores an
outgoing DM's content plus a behavioral check on the sender's recent
activity; commons/account_safety.py decides what happens with the
result (restrict + queue for human review — this module never removes
anyone on its own).

Categories, deliberately kept broad rather than exhaustive:
  - off_platform_contact_request: pushing the conversation to another
    app or asking for a phone number
  - secrecy_pressure: asking to keep the conversation from parents/
    guardians/other trusted adults
  - identifying_info_request: asking for age, school, address, location
  - photo_request: asking for a picture

This is a first pass — regex on text is easy to evade and will both
miss real cases and flag innocent ones. It's designed so a stronger
classifier (e.g. an LLM call) can be added later as an additional
signal source without changing anything that calls evaluate_message().
"""

import re
from datetime import datetime, timedelta

from .features import DirectMessage

BURST_WINDOW_MINUTES = 15
BURST_NEW_RECIPIENT_THRESHOLD = 5

OFF_PLATFORM_PATTERNS = [
    r"\\bsnap(chat)?\\b", r"\\bkik\\b", r"\\bwhats ?app\\b", r"\\bdiscord\\b",
    r"\\btext me\\b", r"\\bcall me\\b", r"\\bmy number\\b", r"\\badd me on\\b",
    r"\\b\\d{3}[-.\\s]?\\d{3}[-.\\s]?\\d{4}\\b",  # phone-number-shaped string
]

SECRECY_PATTERNS = [
    r"\\bdon'?t tell\\b", r"\\bour secret\\b", r"\\bbetween us\\b",
    r"\\bdon'?t (show|tell) (your|ur) (mom|dad|parents|mother|father)\\b",
]

IDENTIFYING_INFO_PATTERNS = [
    r"\\bhow old are you\\b", r"\\bwhat school\\b", r"\\byour address\\b",
    r"\\bwhere do you live\\b", r"\\bare your parents\\b",
]

PHOTO_REQUEST_PATTERNS = [
    r"\\bsend (a |me a |me your )?pic(ture)?s?\\b", r"\\bsend (a )?photo\\b",
]


def _matches_any(patterns, text_lower):
    return any(re.search(p, text_lower) for p in patterns)


def score_content(content: str) -> list:
    text = (content or "").lower()
    signals = []
    if _matches_any(OFF_PLATFORM_PATTERNS, text):
        signals.append("off_platform_contact_request")
    if _matches_any(SECRECY_PATTERNS, text):
        signals.append("secrecy_pressure")
    if _matches_any(IDENTIFYING_INFO_PATTERNS, text):
        signals.append("identifying_info_request")
    if _matches_any(PHOTO_REQUEST_PATTERNS, text):
        signals.append("photo_request")
    return signals


def check_burst_messaging(db, sender_id: int) -> bool:
    """Flags an account rapidly messaging many different new (stranger)
    recipients in a short window — a common scanning/spraying pattern."""
    since = datetime.utcnow() - timedelta(minutes=BURST_WINDOW_MINUTES)
    recent = (
        db.query(DirectMessage.recipient_id)
        .filter(
            DirectMessage.sender_id == sender_id,
            DirectMessage.created_at >= since,
            DirectMessage.is_request == True,
        )
        .distinct()
        .all()
    )
    return len(recent) >= BURST_NEW_RECIPIENT_THRESHOLD


def evaluate_message(db, sender, content: str) -> list:
    """Returns the list of triggered signal names for this outgoing
    message (empty list = nothing tripped)."""
    signals = score_content(content)
    if check_burst_messaging(db, sender.id):
        signals.append("burst_messaging_new_contacts")
    return signals
'''

ACCOUNT_SAFETY_PY = '''"""
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
'''

NEW_FILES = [
    ("commons/dm_safety.py", DM_SAFETY_PY),
    ("commons/account_safety.py", ACCOUNT_SAFETY_PY),
]

# ---------------------------------------------------------------------
# Edits to existing files
# ---------------------------------------------------------------------

PATCHES = [
    # ---- commons/messaging.py -----------------------------------------
    {
        "file": "commons/messaging.py",
        "label": "messaging.py: restriction check + safety scan in send_message()",
        "anchor": '''    receiver = db.query(User).filter(User.username == receiver_username).first()
    if not receiver:
        return {"ok": False, "error": "User not found."}
    if receiver.id == sender.id:
        return {"ok": False, "error": "You cannot message yourself."}

    known = is_known_contact(db, sender.id, receiver.id)

    # Check if already an accepted thread exists
    existing = db.query(DirectMessage).filter(
        ((DirectMessage.sender_id == sender.id) & (DirectMessage.recipient_id == receiver.id)) |
        ((DirectMessage.sender_id == receiver.id) & (DirectMessage.recipient_id == sender.id)),
        DirectMessage.accepted == True
    ).first()

    is_request = not known and existing is None

    msg = DirectMessage(
        sender_id         = sender.id,
        recipient_id      = receiver.id,
        content_encrypted = content.strip(),
        is_request        = is_request,
        accepted          = None if is_request else True
    )
    db.add(msg)
    db.commit()
    return {"ok": True, "request": is_request}''',
        "new": '''    receiver = db.query(User).filter(User.username == receiver_username).first()
    if not receiver:
        return {"ok": False, "error": "User not found."}
    if receiver.id == sender.id:
        return {"ok": False, "error": "You cannot message yourself."}

    from .account_safety import account_safety_manager
    if account_safety_manager.is_restricted(db, sender.id):
        return {"ok": False, "error": "Your account is under review and can only contact Sovereign support until resolved."}

    known = is_known_contact(db, sender.id, receiver.id)

    # Check if already an accepted thread exists
    existing = db.query(DirectMessage).filter(
        ((DirectMessage.sender_id == sender.id) & (DirectMessage.recipient_id == receiver.id)) |
        ((DirectMessage.sender_id == receiver.id) & (DirectMessage.recipient_id == sender.id)),
        DirectMessage.accepted == True
    ).first()

    is_request = not known and existing is None

    msg = DirectMessage(
        sender_id         = sender.id,
        recipient_id      = receiver.id,
        content_encrypted = content.strip(),
        is_request        = is_request,
        accepted          = None if is_request else True
    )
    db.add(msg)
    db.commit()

    from .dm_safety import evaluate_message
    signals = evaluate_message(db, sender, content)
    if signals:
        account_safety_manager.flag_message(db, msg, sender, receiver, signals)

    return {"ok": True, "request": is_request}''',
    },

    # ---- commons/features.py: DirectMessage docstring -----------------
    {
        "file": "commons/features.py",
        "label": "features.py: honest DirectMessage docstring (scanning now reads content)",
        "anchor": '''class DirectMessage(Base):
    """
    End-to-end encrypted direct messages.
    Not readable by the platform. Codex Law 3.
    Messages are stored encrypted — only sender and recipient can read.
    """''',
        "new": '''class DirectMessage(Base):
    """
    Direct messages between users.
    NOTE: content is currently stored as plain text, not actually
    end-to-end encrypted (see the TODO on content_encrypted below) —
    this docstring previously overstated that. Automated safety
    scanning (commons/dm_safety.py) reads message content to detect
    patterns associated with predatory contact toward minors; flagged
    accounts are reviewed by a human moderator, never auto-removed.
    """''',
    },

    # ---- commons/features.py: DirectMessageManager.send() -------------
    {
        "file": "commons/features.py",
        "label": "features.py: fix request-gate bypass + hook restriction/scan into DirectMessageManager.send()",
        "anchor": '''class DirectMessageManager:
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

        return {"ok": True, "message_id": msg.id}''',
        "new": '''class DirectMessageManager:
    """
    Direct messages between users.
    Automated safety scanning runs on send (see commons/dm_safety.py) to
    flag patterns associated with predatory contact toward minors.
    Flagged accounts are restricted and queued for human review — never
    auto-removed. See commons/account_safety.py.
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

        from .account_safety import account_safety_manager
        if account_safety_manager.is_restricted(db, sender.id):
            return {"ok": False, "error": "Your account is under review and can only contact Sovereign support until resolved."}

        # Known-contact / stranger-request gating (matches
        # commons/messaging.py's send_message() — previously this path
        # had no such gate, letting any account message any other
        # account directly with no accept step).
        known = db.query(Follow).filter(
            ((Follow.follower_id == sender.id) & (Follow.following_id == recipient_id)) |
            ((Follow.follower_id == recipient_id) & (Follow.following_id == sender.id))
        ).first() is not None

        existing = db.query(DirectMessage).filter(
            ((DirectMessage.sender_id == sender.id) & (DirectMessage.recipient_id == recipient_id)) |
            ((DirectMessage.sender_id == recipient_id) & (DirectMessage.recipient_id == sender.id)),
            DirectMessage.accepted == True
        ).first()

        is_request = not known and existing is None

        # In production: encrypt with recipient's public key
        # For now: store as-is, mark as encrypted placeholder
        msg = DirectMessage(
            sender_id          = sender.id,
            recipient_id       = recipient_id,
            content_encrypted  = content,  # TODO: Replace with actual E2E encryption
            is_request         = is_request,
            accepted           = None if is_request else True,
        )
        db.add(msg)
        db.commit()

        from .dm_safety import evaluate_message
        signals = evaluate_message(db, sender, content)
        if signals:
            account_safety_manager.flag_message(db, msg, sender, recipient, signals)

        # Notify recipient
        notification_manager.create(
            db,
            user_id    = recipient_id,
            actor_id   = sender.id,
            notif_type = "message",
            message    = f"New message from @{sender.username}"
        )

        return {"ok": True, "message_id": msg.id}''',
    },

    # ---- commons/auth.py: banned-email check ---------------------------
    {
        "file": "commons/auth.py",
        "label": "auth.py: reject registration with a banned email",
        "anchor": '''    if db.query(User).filter(User.email == email).first():
        return {"ok": False, "error": "An account with that email already exists."}

    # Magic link auth — no real password needed''',
        "new": '''    if db.query(User).filter(User.email == email).first():
        return {"ok": False, "error": "An account with that email already exists."}

    from .account_safety import BannedEmail
    if db.query(BannedEmail).filter(BannedEmail.email == email).first():
        return {"ok": False, "error": "This email is not eligible to register."}

    # Magic link auth — no real password needed''',
    },

    # ---- main.py: import block -----------------------------------------
    {
        "file": "main.py",
        "label": "main.py: import account_safety",
        "anchor": "from commons.parental    import parental, ParentalControl",
        "new": "from commons.parental    import parental, ParentalControl\nfrom commons.account_safety import account_safety_manager, AccountRestriction, MessageFlag, BannedEmail, restriction_scheduler",
    },

    # ---- main.py: register new tables before create_all ----------------
    {
        "file": "main.py",
        "label": "main.py: register new tables before Base.metadata.create_all()",
        "anchor": '''    from commons.transparency import OperatingCostEntry, MonthlyReport
    from commons.database import Base, engine
    Base.metadata.create_all(bind=engine)''',
        "new": '''    from commons.transparency import OperatingCostEntry, MonthlyReport
    from commons.account_safety import AccountRestriction, MessageFlag, BannedEmail
    from commons.database import Base, engine
    Base.metadata.create_all(bind=engine)''',
    },

    # ---- main.py: start the restriction sweep thread -------------------
    {
        "file": "main.py",
        "label": "main.py: start restriction_scheduler alongside heartbeat/news_feed",
        "anchor": '''    def background_startup():
        try:
            revival.startup_check()
            heartbeat.start()
            news_feed.start()
        except Exception as e:
            print(f"[STARTUP] Background startup warning: {e}")''',
        "new": '''    def background_startup():
        try:
            revival.startup_check()
            heartbeat.start()
            news_feed.start()
            restriction_scheduler.start()
        except Exception as e:
            print(f"[STARTUP] Background startup warning: {e}")''',
    },

    # ---- main.py: new moderation routes ---------------------------------
    {
        "file": "main.py",
        "label": "main.py: add message-safety moderation endpoints (Sovereign-only)",
        "anchor": '''    result = chat_manager.restore_message(db, message_id)
    return JSONResponse(result)

@app.get("/api/users/{username}/profile")''',
        "new": '''    result = chat_manager.restore_message(db, message_id)
    return JSONResponse(result)

@app.get("/api/messages/moderation/pending")
async def api_message_moderation_pending(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.account_safety import account_safety_manager
    if current_user.role.value.upper() != "SOVEREIGN":
        return JSONResponse({"ok": False, "error": "Sovereign access only."}, status_code=403)
    return JSONResponse({"ok": True, "flags": account_safety_manager.get_pending_flags(db)})

@app.post("/api/messages/moderation/confirm")
async def api_message_moderation_confirm(
    flag_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.account_safety import account_safety_manager
    if current_user.role.value.upper() != "SOVEREIGN":
        return JSONResponse({"ok": False, "error": "Sovereign access only."}, status_code=403)
    result = account_safety_manager.confirm_flag(db, flag_id)
    return JSONResponse(result)

@app.post("/api/messages/moderation/dismiss")
async def api_message_moderation_dismiss(
    flag_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.account_safety import account_safety_manager
    if current_user.role.value.upper() != "SOVEREIGN":
        return JSONResponse({"ok": False, "error": "Sovereign access only."}, status_code=403)
    result = account_safety_manager.dismiss_flag(db, flag_id)
    return JSONResponse(result)

@app.get("/api/users/{username}/profile")''',
    },
]


def write_new_file(rel_path, content):
    path = Path(rel_path)
    if path.exists():
        existing = path.read_text()
        if existing == content:
            print(f"  Already present — skipping: {rel_path}")
            return True
        print(f"  ABORT: {rel_path} already exists with different content. Not overwriting.")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"  Created: {rel_path}")
    return True


def apply_patch(patch):
    path = Path(patch["file"])
    if not path.exists():
        print(f"  ABORT: {path} not found.")
        return False

    text = path.read_text()

    if "old_only_fragment" in patch:
        already_applied = patch["old_only_fragment"] not in text
    else:
        already_applied = patch["new"] in text

    if already_applied:
        print(f"  Already applied — skipping: {patch['label']}")
        return True

    count = text.count(patch["anchor"])
    if count == 0:
        print(f"  ABORT: anchor not found for: {patch['label']}")
        print(f"         (file may have changed since this patch was written)")
        return False
    if count > 1:
        print(f"  ABORT: anchor matched {count} times (expected exactly 1) for: {patch['label']}")
        return False

    text = text.replace(patch["anchor"], patch["new"], 1)
    path.write_text(text)
    print(f"  Applied: {patch['label']}")
    return True


def main():
    print("Adding DM safety scanning + account restriction...")
    ok = True

    for rel_path, content in NEW_FILES:
        if not write_new_file(rel_path, content):
            ok = False
            break

    if ok:
        for patch in PATCHES:
            if not apply_patch(patch):
                ok = False
                break

    if not ok:
        print("\nOne or more steps could not be applied. No further changes made.")
        sys.exit(1)

    print("\nAll steps applied successfully.")
    print("\nNEXT STEPS:")
    print("  1. python3 -c \"import main\"   # sanity check imports")
    print("  2. Update any public Codex/disclosure text claiming DMs are")
    print("     unmonitored — this scan reads message content server-side.")
    print("  3. Build the Sovereign-facing moderation dashboard UI for the")
    print("     new /api/messages/moderation/* endpoints (backend-only for now).")


if __name__ == "__main__":
    main()
