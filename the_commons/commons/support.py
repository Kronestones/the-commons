"""
support.py — The Commons Help & Support

AI-powered support chat. No waiting. No ticket queues.
First response in seconds.

Tier 1 — AI handles:
  - How to use features
  - Account questions
  - Marketplace questions
  - Understanding the Codex
  - Payment and fee questions
  - General platform questions

Tier 2 — Escalates to Circle:
  - Content disputes
  - Account appeals
  - Serious complaints
  - Anything the AI can't resolve

Powers is protected. The Circle governs escalations.
Users always get a response.

Codex Law 1: People First — support matters.
Codex Law 5: Transparency — users know how support works.

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Session
from .database import Base


# ── Models ────────────────────────────────────────────────────────────────────

class SupportTicket(Base):
    """Support ticket — created when AI cannot resolve."""
    __tablename__ = "support_tickets"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=True)
    subject         = Column(String(300), nullable=False)
    description     = Column(Text, nullable=False)
    category        = Column(String(100), default="general")
    status          = Column(String(50), default="open")  # open/in_review/resolved/closed
    ai_attempted    = Column(Boolean, default=True)
    resolution      = Column(Text, default="")
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow)


class SupportMessage(Base):
    """Individual messages in a support conversation."""
    __tablename__ = "support_messages"

    id          = Column(Integer, primary_key=True, index=True)
    ticket_id   = Column(Integer, ForeignKey("support_tickets.id"), nullable=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    role        = Column(String(20), default="user")  # user/ai/circle
    message     = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


# ── Knowledge Base ────────────────────────────────────────────────────────────

KNOWLEDGE_BASE = {
    "feed": {
        "keywords": ["feed", "algorithm", "posts", "see", "show", "why", "transparent"],
        "answer": (
            "The Commons has three feed modes you can choose from:\n\n"
            "• Transparent — every post shows exactly why it appears for you\n"
            "• Chronological — newest posts first, no algorithm\n"
            "• Community Governed — posts valued by the community rise naturally\n\n"
            "You can switch modes anytime in your feed settings. "
            "In transparent mode, each post shows a reason tag like "
            "'Shown because: matches your interest in music.'"
        )
    },
    "like": {
        "keywords": ["like", "vote", "heart", "community", "upvote"],
        "answer": (
            "The like button on The Commons is also the community vote. "
            "When you like a post, you're telling the community it has value — "
            "it's one action that does two things. "
            "Highly liked content rises in the Community Governed feed."
        )
    },
    "fee": {
        "keywords": ["fee", "dollar", "$1", "cost", "charge", "price", "payment", "buy", "sell"],
        "answer": (
            "The Commons charges a flat $1 per sale — not per item. "
            "If you buy 5 things in one checkout, that's still just $1. "
            "You'll also see Stripe's payment processing fee (2.9% + $0.30) "
            "shown transparently at checkout. The Commons takes only the $1 "
            "to cover operating costs. No profit. Ever. Codex Law 12."
        )
    },
    "seller": {
        "keywords": ["sell", "seller", "shop", "store", "business", "list", "product"],
        "answer": (
            "The Commons marketplace is open to individual creators and locally "
            "owned small businesses only. Corporations and publicly traded companies "
            "are not eligible — this is written into the Codex, not just policy.\n\n"
            "To become a seller, go to your profile and tap 'Become a Seller'. "
            "You'll need to confirm you're an individual creator or local business. "
            "The Commons is a facilitator only — all transactions are between "
            "buyer and seller directly."
        )
    },
    "privacy": {
        "keywords": ["privacy", "data", "track", "sell", "personal", "information", "biometric"],
        "answer": (
            "The Commons never sells your data. Ever. Codex Law 3.\n\n"
            "• No advertising — no ad targeting, no behavioral profiling for ads\n"
            "• No biometrics — Codex Law 4\n"
            "• Your preference profile is fully visible to you at any time\n"
            "• You can reset your preference profile anytime\n"
            "• Direct messages are end-to-end encrypted\n"
            "• Translation requests are never stored"
        )
    },
    "parental": {
        "keywords": ["parent", "child", "minor", "kid", "age", "young", "pin", "control"],
        "answer": (
            "The Commons has PIN-based parental controls for minor accounts.\n\n"
            "To set up:\n"
            "1. Go to Settings → Parental Controls\n"
            "2. Enter the minor's account ID\n"
            "3. Set a 4-8 digit PIN\n"
            "4. Approve the account with your PIN\n\n"
            "Once approved, the account automatically filters political content, "
            "restricts commenting on political posts, and applies community value filtering. "
            "No biometrics required. Codex Law 4 and 8."
        )
    },
    "fingerprint": {
        "keywords": ["fingerprint", "verify", "truth", "fact", "news", "political", "removed", "held"],
        "answer": (
            "The Fingerprint is The Commons truth verification system.\n\n"
            "Political and news content is scanned by AI before publishing. "
            "If flagged, a human reviewer checks it against verified sources. "
            "Nothing true is ever accidentally removed — human review is required "
            "before any removal.\n\n"
            "If your content was held, you'll receive a notification. "
            "You have one appeal to the Regional Circle. "
            "If you believe this was an error, tap 'Appeal' on the held post."
        )
    },
    "codex": {
        "keywords": ["codex", "rules", "law", "govern", "circle", "policy"],
        "answer": (
            "The Codex is The Commons constitution — 17 laws embedded directly "
            "in the platform architecture. It's not a policy document that can be "
            "quietly changed. Immutable laws cannot be changed by anyone. "
            "Mutable laws require a two-thirds Circle supermajority.\n\n"
            "You can read all 17 laws at /codex anytime."
        )
    },
    "gifts": {
        "keywords": ["gift", "live", "stream", "creator", "tip", "donate"],
        "answer": (
            "During live streams, viewers can send virtual gifts to creators.\n\n"
            "100% of every gift goes directly to the creator — The Commons takes nothing.\n"
            "You pay Stripe's processing fee (2.9% + $0.30) on top of the gift value.\n\n"
            "Gift values range from ❤️ $0.10 to 🏡 $20.00.\n"
            "No artificial scarcity. No FOMO. Just support for creators you value."
        )
    },
    "account": {
        "keywords": ["account", "login", "password", "register", "username", "profile"],
        "answer": (
            "For account issues:\n\n"
            "• Forgotten password — tap 'Forgot Password' on the login page\n"
            "• Username change — go to Profile → Edit → Display Name\n"
            "• Bio update — go to Profile → Edit → Bio\n"
            "• Delete account — go to Settings → Account → Delete Account\n\n"
            "If you're having trouble logging in and can't reset your password, "
            "submit a support ticket and the Circle will assist."
        )
    },
    "translation": {
        "keywords": ["translate", "language", "spanish", "french", "foreign"],
        "answer": (
            "The Commons supports translation of posts and comments into 29 languages.\n\n"
            "Tap the translate button (🌐) on any post or comment to translate it. "
            "The source language is detected automatically.\n\n"
            "Translation is powered by LibreTranslate — open source, no data stored, "
            "no behavioral profile built from what you translate. Codex Law 3."
        )
    },
    "surplus": {
        "keywords": ["surplus", "donate", "humanitarian", "giving", "money", "profit"],
        "answer": (
            "The Commons operates at cost — no profit. Ever.\n\n"
            "Any money remaining after operating costs are covered is donated to "
            "a humanitarian cause every six months, designated by Sovereign Human "
            "T.L. Powers. Every donation is published publicly at /giving.\n\n"
            "Operating costs are also published monthly at /transparency so "
            "you can see exactly where every dollar goes. Codex Law 17."
        )
    },
}

ESCALATION_TRIGGERS = [
    "appeal", "dispute", "fraud", "stolen", "hacked", "legal",
    "threatening", "harassment", "abuse", "ban", "suspended",
    "circle", "urgent", "emergency", "dangerous"
]


# ── Support Manager ───────────────────────────────────────────────────────────

class SupportManager:

    def get_ai_response(self, message: str) -> dict:
        """
        Generate an AI support response from the knowledge base.
        Returns response and whether escalation is needed.
        """
        message_lower = message.lower()

        # Check escalation triggers first
        needs_escalation = any(
            trigger in message_lower
            for trigger in ESCALATION_TRIGGERS
        )

        if needs_escalation:
            return {
                "response": (
                    "It sounds like your issue needs Circle attention. "
                    "I'm escalating this to the Circle now — they'll review "
                    "your case and respond. Thank you for bringing this to us."
                ),
                "escalate": True,
                "category": "circle_escalation"
            }

        # Search knowledge base
        best_match    = None
        best_score    = 0

        for topic, data in KNOWLEDGE_BASE.items():
            score = sum(
                1 for kw in data["keywords"]
                if kw in message_lower
            )
            if score > best_score:
                best_score = score
                best_match = data

        if best_match and best_score > 0:
            return {
                "response":  best_match["answer"],
                "escalate":  False,
                "category":  "knowledge_base"
            }

        # No match found
        return {
            "response": (
                "I want to make sure you get the right help. "
                "Could you tell me a bit more about what you're experiencing? "
                "For example — is this about your feed, a post, a purchase, "
                "your account, or something else?\n\n"
                "If I can't resolve it, I'll connect you with the Circle."
            ),
            "escalate":  False,
            "category":  "clarification_needed"
        }

    def create_ticket(self, db: Session,
                      user_id: Optional[int],
                      subject: str,
                      description: str,
                      category: str = "general") -> dict:
        """Create a support ticket for Circle review."""
        ticket = SupportTicket(
            user_id     = user_id,
            subject     = subject,
            description = description,
            category    = category,
            status      = "open",
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)

        print(f"[SUPPORT] Ticket {ticket.id} created — {category}")
        return {
            "ok":        True,
            "ticket_id": ticket.id,
            "message":   (
                "Your ticket has been submitted to the Circle. "
                "You'll receive a response as soon as possible. "
                "Ticket ID: " + str(ticket.id)
            )
        }

    def save_message(self, db: Session,
                     ticket_id: Optional[int],
                     user_id: Optional[int],
                     role: str,
                     message: str) -> None:
        """Save a support chat message."""
        db.add(SupportMessage(
            ticket_id = ticket_id,
            user_id   = user_id,
            role      = role,
            message   = message,
        ))
        db.commit()

    def get_faq(self) -> list:
        """Return FAQ list from knowledge base."""
        faq_map = {
            "feed":        "How does the feed work?",
            "fee":         "What does The Commons charge?",
            "privacy":     "What data does The Commons collect?",
            "fingerprint": "Why was my post held for review?",
            "parental":    "How do parental controls work?",
            "seller":      "How do I sell on The Commons?",
            "gifts":       "How do live gifts work?",
            "surplus":     "What happens to surplus money?",
            "codex":       "What is the Codex?",
            "translation": "How do I translate posts?",
        }
        return [
            {"question": q, "answer": KNOWLEDGE_BASE[k]["answer"]}
            for k, q in faq_map.items()
        ]

    def get_open_tickets(self, db: Session) -> list:
        """Get all open tickets for Circle review."""
        tickets = db.query(SupportTicket).filter(
            SupportTicket.status == "open"
        ).order_by(SupportTicket.created_at).all()

        return [
            {
                "id":          t.id,
                "subject":     t.subject,
                "category":    t.category,
                "created_at":  t.created_at.isoformat(),
                "description": t.description[:200],
            }
            for t in tickets
        ]

    def resolve_ticket(self, db: Session,
                       ticket_id: int,
                       resolution: str) -> dict:
        """Circle resolves a ticket."""
        ticket = db.query(SupportTicket).filter(
            SupportTicket.id == ticket_id
        ).first()
        if not ticket:
            return {"ok": False, "error": "Ticket not found."}

        ticket.status     = "resolved"
        ticket.resolution = resolution
        ticket.updated_at = datetime.utcnow()
        db.commit()
        return {"ok": True}


support_manager = SupportManager()
