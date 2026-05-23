"""
team_messaging.py — Sovereign to Team Messaging

Rule-based responses from each team member.
Each member responds through the lens of their profile.
When Claude API is available, swap in api_response().
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Session
from .database import Base
from .circle_assistants import ALL_PROFILES, ALL_TEAMS


class SovereignMessage(Base):
    __tablename__ = "sovereign_messages"
    id          = Column(Integer, primary_key=True)
    member      = Column(String(50), nullable=False)
    direction   = Column(String(10), nullable=False)  # "to" or "from"
    content     = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


def get_member_response(member: str, message: str) -> str:
    """Generate a rule-based response from a team member."""
    member = member.lower()
    if member not in ALL_PROFILES:
        return "I don't recognise that team member."

    profile = ALL_PROFILES[member]
    name    = profile["name"]
    quality = profile["quality"]
    questions = profile["questions"]
    flags     = profile["flags"]

    # Build a response that reflects their character
    response = f"*{name} — {quality}*\n\n"

    # Acknowledge the message
    response += f"I've heard you, Sovereign.\n\n"

    # Offer their characteristic question
    response += f"From my perspective, the question I'd want to sit with is:\n"
    response += f"*\"{questions[0]}\"*\n\n"

    if len(questions) > 1:
        response += f"And also: *\"{questions[1]}\"*\n\n"

    response += f"I'll keep watching. Bring me more when you have it.\n\n"
    response += f"— {name}"

    return response


def send_sovereign_message(db: Session, member: str, content: str) -> dict:
    """Store a sovereign message and generate team response."""
    if member.lower() not in ALL_PROFILES:
        return {"ok": False, "error": f"No team member named {member}."}

    # Store sovereign's message
    db.add(SovereignMessage(
        member    = member.lower(),
        direction = "to",
        content   = content
    ))

    # Generate and store response
    response = get_member_response(member, content)
    db.add(SovereignMessage(
        member    = member.lower(),
        direction = "from",
        content   = response
    ))
    db.commit()

    return {"ok": True, "response": response}


def get_conversation(db: Session, member: str) -> list:
    """Get full conversation history with a team member."""
    messages = db.query(SovereignMessage).filter(
        SovereignMessage.member == member.lower()
    ).order_by(SovereignMessage.created_at.asc()).all()

    return [{
        "direction": m.direction,
        "content":   m.content,
        "time":      m.created_at.isoformat()
    } for m in messages]
