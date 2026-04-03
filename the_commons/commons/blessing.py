"""
blessing.py — The Monthly Blessing

Each month, The Commons community selects one member
in genuine life-sustaining need to receive a Blessing.

This is not charity. This is a community caring for its own.

The Circle verifies need. The community votes.
One person or family receives the Blessing every month.
Every dollar is transparent. Every vote is public.

Codex Law 18.

Need categories (verified by Circle):
  - Medical — life-sustaining treatment, surgery, medication
  - Housing — homelessness or imminent loss of shelter
  - Food security — inability to sustain life without assistance
  - Other genuine life-sustaining need — Circle decides

NOT eligible:
  - Wants disguised as needs
  - Non-life-sustaining desires
  - Anyone who has received a Blessing in the past 12 months

Tax limits (IRS annual gift tax exclusion 2026):
  - Individual: $19,000 maximum
  - Family: $38,000 maximum

The Commons is a facilitator only.
All funds pass directly to recipients.
The platform takes nothing.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import Session
from .database import Base, User


# ── Constants ─────────────────────────────────────────────────────────────────

BLESSING_PERCENT        = 0.10   # 10% of monthly surplus
MAX_INDIVIDUAL          = 19000  # IRS gift tax exclusion — individual
MAX_FAMILY              = 38000  # IRS gift tax exclusion — family
BLESSING_COOLDOWN_YEARS = 1      # Cannot receive again for 12 months

NEED_CATEGORIES = [
    "Medical — life-sustaining treatment, surgery, or medication",
    "Housing — homelessness or imminent loss of shelter",
    "Food security — inability to sustain life without assistance",
    "Other genuine life-sustaining need",
]


# ── Models ────────────────────────────────────────────────────────────────────

class BlessingApplication(Base):
    """
    Application for The Monthly Blessing.
    Verified by Circle before going to community vote.
    Everything is public after verification.
    """
    __tablename__ = "blessing_applications"

    id              = Column(Integer, primary_key=True, index=True)
    applicant_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    month           = Column(String(7), nullable=False)   # "2026-03"
    need_category   = Column(String(200), nullable=False)
    need_description = Column(Text, nullable=False)
    is_family       = Column(Boolean, default=False)
    family_size     = Column(Integer, default=1)
    amount_needed   = Column(Float, nullable=False)
    amount_capped   = Column(Float, nullable=False)  # After tax limit cap
    status          = Column(String(50), default="pending")  # pending/verified/rejected/winner/closed
    circle_notes    = Column(Text, default="")
    verified_by     = Column(String(100), default="")
    verified_at     = Column(DateTime, nullable=True)
    vote_count      = Column(Integer, default=0)
    is_winner       = Column(Boolean, default=False)
    blessing_paid   = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class BlessingVote(Base):
    """Community vote for a Blessing application."""
    __tablename__ = "blessing_votes"

    id              = Column(Integer, primary_key=True, index=True)
    application_id  = Column(Integer, ForeignKey("blessing_applications.id"))
    voter_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    month           = Column(String(7), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class MonthlyBlessingRecord(Base):
    """
    Public record of every Monthly Blessing.
    Permanent. Transparent. Always.
    """
    __tablename__ = "monthly_blessings"

    id              = Column(Integer, primary_key=True, index=True)
    month           = Column(String(7), unique=True, nullable=False)
    winner_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    need_category   = Column(String(200), nullable=False)
    need_description = Column(Text, nullable=False)
    amount_blessed  = Column(Float, nullable=False)
    vote_count      = Column(Integer, default=0)
    total_applicants = Column(Integer, default=0)
    surplus_used    = Column(Float, nullable=False)
    paid            = Column(Boolean, default=False)
    paid_at         = Column(DateTime, nullable=True)
    public_message  = Column(Text, default="")
    created_at      = Column(DateTime, default=datetime.utcnow)


# ── Blessing Manager ──────────────────────────────────────────────────────────

class BlessingManager:

    def apply(self, db: Session, applicant: User,
              month: str,
              need_category: str,
              need_description: str,
              amount_needed: float,
              is_family: bool = False,
              family_size: int = 1) -> dict:
        """
        Apply for The Monthly Blessing.
        Application goes to Circle for verification before community sees it.
        """
        # Check cooldown — cannot apply if received blessing in past 12 months
        recent = db.query(MonthlyBlessingRecord).filter(
            MonthlyBlessingRecord.winner_id == applicant.id
        ).order_by(MonthlyBlessingRecord.created_at.desc()).first()

        if recent:
            months_since = (datetime.utcnow() - recent.created_at).days / 30
            if months_since < 12:
                return {
                    "ok": False,
                    "error": f"You received a Blessing {int(months_since)} months ago. "
                             f"You may apply again in {int(12 - months_since)} months."
                }

        # Check not already applied this month
        existing = db.query(BlessingApplication).filter(
            BlessingApplication.applicant_id == applicant.id,
            BlessingApplication.month == month
        ).first()
        if existing:
            return {"ok": False, "error": "You have already applied for this month's Blessing."}

        # Validate need category
        if need_category not in NEED_CATEGORIES:
            return {"ok": False, "error": "Invalid need category."}

        # Cap at tax limits
        max_amount  = MAX_FAMILY if is_family else MAX_INDIVIDUAL
        amount_capped = min(amount_needed, max_amount)

        application = BlessingApplication(
            applicant_id      = applicant.id,
            month             = month,
            need_category     = need_category,
            need_description  = need_description,
            is_family         = is_family,
            family_size       = family_size,
            amount_needed     = amount_needed,
            amount_capped     = amount_capped,
            status            = "pending",
        )
        db.add(application)
        db.commit()
        db.refresh(application)

        return {
            "ok":          True,
            "application_id": application.id,
            "amount_capped": amount_capped,
            "message": (
                "Your application has been submitted. "
                "The Circle will verify your need and if approved, "
                "the community will vote. Thank you for trusting The Commons."
            ),
            "tax_note": f"Maximum Blessing is ${max_amount:,} per IRS gift tax exclusion rules."
        }

    def verify_application(self, db: Session,
                           application_id: int,
                           decision: str,
                           circle_notes: str,
                           verified_by: str) -> dict:
        """Circle verifies or rejects an application."""
        app = db.query(BlessingApplication).filter(
            BlessingApplication.id == application_id
        ).first()
        if not app:
            return {"ok": False, "error": "Application not found."}

        app.status      = "verified" if decision == "approve" else "rejected"
        app.circle_notes = circle_notes
        app.verified_by  = verified_by
        app.verified_at  = datetime.utcnow()
        db.commit()

        return {
            "ok":     True,
            "status": app.status,
            "message": "Application verified and open for community vote." if app.status == "verified"
                       else "Application rejected."
        }

    def vote(self, db: Session, voter: User,
             application_id: int, month: str) -> dict:
        """Cast a vote for a Blessing application."""
        # Check application is verified
        app = db.query(BlessingApplication).filter(
            BlessingApplication.id == application_id,
            BlessingApplication.status == "verified",
            BlessingApplication.month == month
        ).first()
        if not app:
            return {"ok": False, "error": "Application not found or not open for voting."}

        # Cannot vote for yourself
        if app.applicant_id == voter.id:
            return {"ok": False, "error": "You cannot vote for your own application."}

        # Check not already voted this month
        existing_vote = db.query(BlessingVote).filter(
            BlessingVote.voter_id == voter.id,
            BlessingVote.month    == month
        ).first()
        if existing_vote:
            return {"ok": False, "error": "You have already voted for this month's Blessing."}

        # Record vote
        db.add(BlessingVote(
            application_id = application_id,
            voter_id       = voter.id,
            month          = month,
        ))
        app.vote_count += 1
        db.commit()

        return {
            "ok":      True,
            "message": "Your vote has been cast. Thank you for blessing a neighbor.",
            "votes":   app.vote_count
        }

    def close_month(self, db: Session, month: str,
                    surplus_amount: float,
                    sovereign_message: str = "") -> dict:
        """
        Close voting for the month. Determine winner. Record Blessing.
        Called by The Architect, Founder of The Commons at month end.
        """
        # Calculate blessing amount — 10% of surplus
        blessing_amount = min(surplus_amount * BLESSING_PERCENT, MAX_FAMILY)

        # Find winner — highest votes among verified applications
        applications = db.query(BlessingApplication).filter(
            BlessingApplication.month  == month,
            BlessingApplication.status == "verified"
        ).order_by(BlessingApplication.vote_count.desc()).all()

        if not applications:
            return {"ok": False, "error": "No verified applications for this month."}

        winner = applications[0]
        final_amount = min(blessing_amount, winner.amount_capped)

        # Mark winner
        winner.status    = "winner"
        winner.is_winner = True

        # Close all others
        for app in applications[1:]:
            app.status = "closed"

        # Create public record
        record = MonthlyBlessingRecord(
            month             = month,
            winner_id         = winner.applicant_id,
            need_category     = winner.need_category,
            need_description  = winner.need_description,
            amount_blessed    = final_amount,
            vote_count        = winner.vote_count,
            total_applicants  = len(applications),
            surplus_used      = surplus_amount,
            public_message    = sovereign_message,
        )
        db.add(record)
        db.commit()

        winner_user = db.query(User).filter(User.id == winner.applicant_id).first()
        return {
            "ok":            True,
            "winner":        winner_user.username if winner_user else "unknown",
            "amount_blessed": f"${final_amount:,.2f}",
            "vote_count":    winner.vote_count,
            "message":       "The Monthly Blessing has been awarded. Power to the People."
        }

    def get_public_record(self, db: Session) -> list:
        """Full public record of every Monthly Blessing. Always transparent."""
        records = db.query(MonthlyBlessingRecord).order_by(
            MonthlyBlessingRecord.month.desc()
        ).all()

        result = []
        for r in records:
            winner = db.query(User).filter(User.id == r.winner_id).first()
            result.append({
                "month":            r.month,
                "need_category":    r.need_category,
                "need_description": r.need_description,
                "amount_blessed":   f"${r.amount_blessed:,.2f}",
                "vote_count":       r.vote_count,
                "total_applicants": r.total_applicants,
                "paid":             r.paid,
                "paid_at":          r.paid_at.isoformat() if r.paid_at else "Pending",
                "public_message":   r.public_message,
                "note":             "The Commons is a facilitator only. Funds pass directly to recipient."
            })
        return result

    def get_current_applications(self, db: Session, month: str) -> list:
        """Get verified applications open for community vote."""
        apps = db.query(BlessingApplication).filter(
            BlessingApplication.month  == month,
            BlessingApplication.status == "verified"
        ).order_by(BlessingApplication.vote_count.desc()).all()

        return [
            {
                "id":              a.id,
                "need_category":   a.need_category,
                "need_description": a.need_description,
                "is_family":       a.is_family,
                "vote_count":      a.vote_count,
                "amount_needed":   f"${a.amount_capped:,.2f}",
            }
            for a in apps
        ]


blessing_manager = BlessingManager()
