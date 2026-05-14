"""
messaging.py — Direct Messages

Uses Follow and DirectMessage from features.py.
Known contacts (either follows the other) → straight to inbox.
Strangers → message request, user accepts or ignores.

Codex Law 3: No surveillance. No data selling.
Power to the People.
"""

from sqlalchemy.orm import Session
from .database import User
from .features import Follow, DirectMessage, follow_manager


def is_known_contact(db: Session, user_a_id: int, user_b_id: int) -> bool:
    return db.query(Follow).filter(
        ((Follow.follower_id == user_a_id) & (Follow.following_id == user_b_id)) |
        ((Follow.follower_id == user_b_id) & (Follow.following_id == user_a_id))
    ).first() is not None


def send_message(db: Session, sender: User, receiver_username: str, content: str) -> dict:
    if not content or not content.strip():
        return {"ok": False, "error": "Message cannot be empty."}
    if len(content) > 2000:
        return {"ok": False, "error": "Message too long (max 2000 characters)."}

    receiver = db.query(User).filter(User.username == receiver_username).first()
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
    return {"ok": True, "request": is_request}


def get_inbox(db: Session, user: User) -> list:
    msgs = db.query(DirectMessage).filter(
        (DirectMessage.recipient_id == user.id) | (DirectMessage.sender_id == user.id),
        DirectMessage.accepted == True
    ).order_by(DirectMessage.created_at.desc()).all()

    seen = {}
    for m in msgs:
        other_id = m.sender_id if m.recipient_id == user.id else m.recipient_id
        if other_id not in seen:
            other = db.query(User).filter(User.id == other_id).first()
            seen[other_id] = {
                "username":     other.username if other else "unknown",
                "last_message": m.content_encrypted,
                "unread":       m.recipient_id == user.id and not m.is_read,
                "time":         m.created_at.isoformat()
            }
    return list(seen.values())


def get_requests(db: Session, user: User) -> list:
    reqs = db.query(DirectMessage).filter(
        DirectMessage.recipient_id == user.id,
        DirectMessage.is_request   == True,
        DirectMessage.accepted     == None
    ).order_by(DirectMessage.created_at.desc()).all()

    result = []
    for m in reqs:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        result.append({
            "id":       m.id,
            "username": sender.username if sender else "unknown",
            "preview":  m.content_encrypted[:100],
            "time":     m.created_at.isoformat()
        })
    return result


def accept_request(db: Session, user: User, message_id: int) -> dict:
    msg = db.query(DirectMessage).filter(
        DirectMessage.id           == message_id,
        DirectMessage.recipient_id == user.id,
        DirectMessage.is_request   == True
    ).first()
    if not msg:
        return {"ok": False, "error": "Request not found."}
    msg.accepted = True
    db.commit()
    return {"ok": True}


def decline_request(db: Session, user: User, message_id: int) -> dict:
    msg = db.query(DirectMessage).filter(
        DirectMessage.id           == message_id,
        DirectMessage.recipient_id == user.id,
        DirectMessage.is_request   == True
    ).first()
    if not msg:
        return {"ok": False, "error": "Request not found."}
    msg.accepted = False
    db.commit()
    return {"ok": True}


def get_conversation(db: Session, user: User, other_username: str) -> list:
    other = db.query(User).filter(User.username == other_username).first()
    if not other:
        return []
    msgs = db.query(DirectMessage).filter(
        ((DirectMessage.sender_id == user.id) & (DirectMessage.recipient_id == other.id)) |
        ((DirectMessage.sender_id == other.id) & (DirectMessage.recipient_id == user.id)),
        DirectMessage.accepted == True
    ).order_by(DirectMessage.created_at.asc()).all()

    for m in msgs:
        if m.recipient_id == user.id and not m.is_read:
            m.is_read = True
    db.commit()

    return [{
        "id":      m.id,
        "sender":  db.query(User).filter(User.id == m.sender_id).first().username,
        "content": m.content_encrypted,
        "time":    m.created_at.isoformat(),
        "mine":    m.sender_id == user.id
    } for m in msgs]
