"""
team_messaging.py — Sovereign to Team Messaging

Rule-based responses from each team member.
Each member responds through the lens of their profile.
When Claude API is available, swap in api_response().
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Session
from .database import Base
from .circle_assistants import ALL_PROFILES, ALL_TEAMS
from .config import config


class SovereignMessage(Base):
    __tablename__ = "sovereign_messages"
    id          = Column(Integer, primary_key=True)
    member      = Column(String(50), nullable=False)
    direction   = Column(String(10), nullable=False)  # "to" or "from"
    content     = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


def api_response(member: str, message: str, history: list = None) -> Optional[str]:
    """
    Generate a real response from a team member using the Anthropic API.
    Returns None if no API key is configured, or if the call fails —
    callers should fall back to get_member_response() in that case.

    To activate: set ANTHROPIC_API_KEY in Render's environment variables.
    Optionally set ANTHROPIC_MODEL (defaults to claude-haiku-4-5-20251001).
    """
    if not config.anthropic_api_key:
        return None

    member = member.lower()
    if member not in ALL_PROFILES:
        return None

    profile = ALL_PROFILES[member]

    system_prompt = (
        f"You are {profile['name']}, known as \"{profile['quality']}\" on The Commons "
        f"platform's moderation team. {profile['description']} "
        f"You are speaking directly with the Sovereign (the platform's founder). "
        f"Respond in character, briefly and naturally — a few sentences, not a report. "
        f"Do not break character or mention that you are an AI assistant."
    )

    try:
        import requests
        payload_messages = []
        if history:
            for h in history:
                role = "assistant" if h.get("direction") == "from" else "user"
                payload_messages.append({"role": role, "content": h.get("content", "")})
        payload_messages.append({"role": "user", "content": message})

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": config.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.anthropic_model,
                "max_tokens": 400,
                "system": system_prompt,
                "messages": payload_messages,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        return text.strip() or None
    except Exception as e:
        print(f"[TEAM_MESSAGING] api_response error for {member}: {e}")
        return None


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
    """Store a sovereign message and generate team response.

    Tries the real Anthropic API first (if ANTHROPIC_API_KEY is set in
    Render's environment). Falls back to the rule-based response if no
    key is configured or the API call fails for any reason.
    """
    if member.lower() not in ALL_PROFILES:
        return {"ok": False, "error": f"No team member named {member}."}

    # Store sovereign's message
    db.add(SovereignMessage(
        member    = member.lower(),
        direction = "to",
        content   = content
    ))

    # Pull recent history for conversational context (used only if API is active)
    history = get_conversation(db, member)

    # Try real API response first; fall back to rule-based if unavailable
    response = api_response(member, content, history)
    if response is None:
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
