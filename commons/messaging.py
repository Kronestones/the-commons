"""
messaging.py — Direct Messages

Known contacts (mutual follows) → straight to inbox.
Strangers → message request, user accepts or ignores.

No dark patterns. No read receipts without consent.
Power to the People.
"""

from datetime import datetime
from sqlalchemy.orm import Session
from .database import User, Follow, DirectMessage


def is_following(db: Session, follower_id: int, following_id: int) -> bool:
    return db.query(Follow).filter(
        Follow.follower_id == follower_id,
        Follow.following_id == following_id
    ).first() is not None


def is_known_contact(db: Session, user_a_id: int, user_b_id: int) -> bool:
    """Known contact = either follows the other."""
    return (
        is_following(db, user_a_id, user_b_id) or
        is_following(db, user_b_id, user_a_id)
    )


def follow_user(db: Session, follower: User, username: str) -> dict:
    target = db.query(User).filter(User.username == username).first()
    if not target:
        return {"ok": False, "error": "User not found."}
    if target.id == follower.id:
        return {"ok": False, "error": "You cannot follow yourself."}
    existing = db.query(Follow).filter(
        Follow.follower_id == follower.id,
        Follow.following_id == target.id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"ok": True, "following": False}
    db.add(Follow(follower_id=follower.id, following_id=target.id))
    db.commit()
    return {"ok": True, "following": True}


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

    # Check if there's already an accepted thread
    existing = db.query(DirectMessage).filter(
        DirectMessage.sender_id == sender.id,
        DirectMessage.receiver_id == receiver.id,
        DirectMessage.accepted == True
    ).first()
    if not existing:
        existing = db.query(DirectMessage).filter(
            DirectMessage.sender_id == receiver.id,
            DirectMessage.receiver_id == sender.id,
            DirectMessage.accepted == True
        ).first()

    is_request = not known and existing is None

    msg = DirectMessage(
        sender_id   = sender.id,
        receiver_id = receiver.id,
        content     = content.strip(),
        request     = is_request,
        accepted    = None if is_request else True
    )
    db.add(msg)
    db.commit()
    return {"ok": True, "request": is_request}


def get_inbox(db: Session, user: User) -> list:
    """Get accepted conversations."""
    msgs = db.query(DirectMessage).filter(
        (
            (DirectMessage.receiver_id == user.id) |
            (DirectMessage.sender_id == user.id)
        ),
        DirectMessage.accepted == True
    ).order_by(DirectMessage.created_at.desc()).all()

    # Group by conversation partner
    seen = {}
    for m in msgs:
        other_id = m.sender_id if m.receiver_id == user.id else m.receiver_id
        if other_id not in seen:
            other = db.query(User).filter(User.id == other_id).first()
            seen[other_id] = {
                "username":   other.username if other else "unknown",
                "last_message": m.content,
                "unread":     m.receiver_id == user.id and not m.read,
                "time":       m.created_at.isoformat()
            }
    return list(seen.values())


def get_requests(db: Session, user: User) -> list:
    """Get pending message requests."""
    reqs = db.query(DirectMessage).filter(
        DirectMessage.receiver_id == user.id,
        DirectMessage.request == True,
        DirectMessage.accepted == None
    ).order_by(DirectMessage.created_at.desc()).all()

    result = []
    for m in reqs:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        result.append({
            "id":       m.id,
            "username": sender.username if sender else "unknown",
            "preview":  m.content[:100],
            "time":     m.created_at.isoformat()
        })
    return result


def accept_request(db: Session, user: User, message_id: int) -> dict:
    msg = db.query(DirectMessage).filter(
        DirectMessage.id == message_id,
        DirectMessage.receiver_id == user.id,
        DirectMessage.request == True
    ).first()
    if not msg:
        return {"ok": False, "error": "Request not found."}
    msg.accepted = True
    db.commit()
    return {"ok": True}


def decline_request(db: Session, user: User, message_id: int) -> dict:
    msg = db.query(DirectMessage).filter(
        DirectMessage.id == message_id,
        DirectMessage.receiver_id == user.id,
        DirectMessage.request == True
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
        (
            (DirectMessage.sender_id == user.id) &
            (DirectMessage.receiver_id == other.id)
        ) | (
            (DirectMessage.sender_id == other.id) &
            (DirectMessage.receiver_id == user.id)
        ),
        DirectMessage.accepted == True
    ).order_by(DirectMessage.created_at.asc()).all()

    # Mark as read
    for m in msgs:
        if m.receiver_id == user.id and not m.read:
            m.read = True
    db.commit()

    return [{
        "id":        m.id,
        "sender":    db.query(User).filter(User.id == m.sender_id).first().username,
        "content":   m.content,
        "time":      m.created_at.isoformat(),
        "mine":      m.sender_id == user.id
    } for m in msgs]
