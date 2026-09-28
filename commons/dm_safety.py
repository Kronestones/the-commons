"""
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
    r"\bsnap(chat)?\b", r"\bkik\b", r"\bwhats ?app\b", r"\bdiscord\b",
    r"\btext me\b", r"\bcall me\b", r"\bmy number\b", r"\badd me on\b",
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # phone-number-shaped string
]

SECRECY_PATTERNS = [
    r"\bdon'?t tell\b", r"\bour secret\b", r"\bbetween us\b",
    r"\bdon'?t (show|tell) (your|ur) (mom|dad|parents|mother|father)\b",
]

IDENTIFYING_INFO_PATTERNS = [
    r"\bhow old are you\b", r"\bwhat school\b", r"\byour address\b",
    r"\bwhere do you live\b", r"\bare your parents\b",
]

PHOTO_REQUEST_PATTERNS = [
    r"\bsend (a |me a |me your )?pic(ture)?s?\b", r"\bsend (a )?photo\b",
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
