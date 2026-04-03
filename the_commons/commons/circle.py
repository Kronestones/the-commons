"""
circle.py — The Circle

Democratic governance of The Commons.
The Circle governs how the platform runs.
The Sovereign protects what the platform is.

Global Circle: 7-11 members, elected by all users
Regional Circles: 5-7 members per region
Community Circles: 3-5 members per community

Voting thresholds:
  Standard majority  : >50% — day to day decisions
  Supermajority      : 67%  — Codex amendments, removals, major changes

Dissent is always recorded.
Minority opinion matters.
Every decision comes with a reason.
No black boxes.

— The Architect, Founder of The Commons · The Commons · 2026
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from .database import (
    CircleMember, CircleDecision, Post, PostStatus,
    User, UserRole, VoteChoice
)
from .config import config

MAJORITY      = config.min_circle_size and 0.51
SUPERMAJORITY = 0.67
MIN_VOTES     = 2


class CircleGovernance:

    # ── Decisions ─────────────────────────────────────────────────────────────

    def open_decision(self, db: Session, subject: str,
                      decision_type: str, post_id: int = None) -> dict:
        decision = CircleDecision(
            subject       = subject,
            decision_type = decision_type,
            post_id       = post_id,
            created_at    = datetime.utcnow(),
        )
        db.add(decision)
        db.commit()
        db.refresh(decision)
        print(f"[CIRCLE] Decision opened: {subject} ({decision_type})")
        return {"ok": True, "decision_id": decision.id}

    def cast_vote(self, db: Session, decision_id: int,
                  member: User, vote: str, note: str = "") -> dict:
        """Cast a vote. Dissent is always recorded."""
        decision = db.query(CircleDecision).filter(
            CircleDecision.id == decision_id
        ).first()

        if not decision:
            return {"ok": False, "error": "Decision not found."}
        if decision.closed_at:
            return {"ok": False, "error": "This decision is already closed."}

        vote = vote.upper()
        if vote not in ("AYE", "NAY", "ABSTAIN"):
            return {"ok": False, "error": "Vote must be AYE, NAY, or ABSTAIN."}

        if vote == "AYE":
            decision.ayes += 1
        elif vote == "NAY":
            decision.nays += 1
            # Record dissent — minority opinion always preserved
            if note:
                dissent = decision.dissent_notes or ""
                decision.dissent_notes = dissent + f"\n[{member.username}]: {note}"
        else:
            decision.abstentions += 1

        db.commit()

        # Update Circle member vote count
        circle_member = db.query(CircleMember).filter(
            CircleMember.user_id == member.id
        ).first()
        if circle_member:
            circle_member.votes_cast += 1
            db.commit()

        return {"ok": True, "vote": vote}

    def evaluate(self, db: Session, decision_id: int,
                 threshold: float = MAJORITY) -> dict:
        """Evaluate whether a majority has been reached."""
        decision = db.query(CircleDecision).filter(
            CircleDecision.id == decision_id
        ).first()

        if not decision:
            return {"ok": False, "error": "Decision not found."}

        total = decision.ayes + decision.nays + decision.abstentions
        if total < MIN_VOTES:
            return {
                "ok": True,
                "status": "pending",
                "message": f"Waiting for more votes ({total}/{MIN_VOTES} minimum)."
            }

        ratio = decision.ayes / total if total > 0 else 0

        if ratio >= threshold:
            return self._close_decision(db, decision, "PASSED", ratio)
        elif (decision.nays / total) >= threshold:
            return self._close_decision(db, decision, "FAILED", ratio)
        else:
            return {
                "ok": True,
                "status": "pending",
                "message": f"No majority yet. {ratio:.0%} for, {threshold:.0%} needed."
            }

    def _close_decision(self, db: Session, decision: CircleDecision,
                        outcome: str, ratio: float) -> dict:
        decision.outcome    = outcome
        decision.closed_at  = datetime.utcnow()
        db.commit()
        print(f"[CIRCLE] Decision {decision.id} closed: {outcome} ({ratio:.0%})")
        return {
            "ok":      True,
            "status":  "closed",
            "outcome": outcome,
            "ratio":   ratio,
        }

    # ── Appeal ────────────────────────────────────────────────────────────────

    def open_appeal(self, db: Session, post_id: int, reason: str) -> dict:
        """
        Poster appeals a removal to the Regional Circle.
        One appeal available. Circle decision is final.
        """
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return {"ok": False, "error": "Post not found."}
        if post.status != PostStatus.REMOVED:
            return {"ok": False, "error": "Only removed posts can be appealed."}

        # Check no prior appeal exists
        prior = db.query(CircleDecision).filter(
            CircleDecision.post_id == post_id,
            CircleDecision.decision_type == "appeal"
        ).first()
        if prior:
            return {"ok": False, "error": "One appeal has already been submitted. The Circle's decision is final."}

        post.status = PostStatus.APPEALED
        db.commit()

        result = self.open_decision(
            db,
            subject       = f"Appeal: Post {post_id}",
            decision_type = "appeal",
            post_id       = post_id,
        )

        print(f"[CIRCLE] Appeal opened for post {post_id}. Reason: {reason}")
        return result

    # ── Circle Membership ─────────────────────────────────────────────────────

    def get_members(self, db: Session, region: str = "global") -> list:
        return (
            db.query(CircleMember)
            .filter(CircleMember.region == region)
            .all()
        )

    def member_count(self, db: Session, region: str = "global") -> int:
        return (
            db.query(CircleMember)
            .filter(CircleMember.region == region)
            .count()
        )

    def is_quorum(self, db: Session, region: str = "global") -> bool:
        return self.member_count(db, region) >= config.min_circle_size

    def add_member(self, db: Session, user: User,
                   region: str = "global", seat_type: str = "global") -> dict:
        existing = db.query(CircleMember).filter(
            CircleMember.user_id == user.id
        ).first()
        if existing:
            return {"ok": False, "error": f"{user.username} is already a Circle member."}

        member = CircleMember(
            user_id   = user.id,
            seat_type = seat_type,
            region    = region,
        )
        db.add(member)
        user.role = UserRole.CIRCLE
        db.commit()
        print(f"[CIRCLE] {user.username} joined the Circle ({region}).")
        return {"ok": True}

    def pending_decisions(self, db: Session) -> list:
        return (
            db.query(CircleDecision)
            .filter(CircleDecision.closed_at == None)
            .order_by(CircleDecision.created_at)
            .all()
        )


circle = CircleGovernance()
