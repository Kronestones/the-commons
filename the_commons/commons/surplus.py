"""
surplus.py — The Commons Surplus Donation System

Any money left over after operating costs goes to humanitarian causes.
Not to shareholders. Not to executives. Not sitting in an account growing.
To people who need it.

Every 6 months, The Architect, Founder of The Commons designates a cause.
The donation amount and recipient are published publicly on the platform.
Full transparency. No exceptions.

This is Codex Law 17.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import Session
from .database import Base, engine

DONATION_PERIOD_MONTHS = 6   # Every 6 months


class SurplusDonation(Base):
    """
    Record of every surplus donation made.
    All public. All transparent. Forever.
    """
    __tablename__ = "surplus_donations"

    id              = Column(Integer, primary_key=True, index=True)
    period_start    = Column(DateTime, nullable=False)
    period_end      = Column(DateTime, nullable=False)
    operating_costs = Column(Float, nullable=False)   # What it cost to run
    total_collected = Column(Float, nullable=False)   # Total $1 fees collected
    surplus_amount  = Column(Float, nullable=False)   # What was left over
    cause_name      = Column(String(300), nullable=False)
    cause_url       = Column(String(500), default="")
    cause_description = Column(Text, default="")
    donated_at      = Column(DateTime, nullable=True)
    confirmed       = Column(Boolean, default=False)  # Sovereign confirms donation made
    public_note     = Column(Text, default="")        # Message to the community
    designated_by   = Column(String(100), default="The Architect, Founder of The Commons")


class SurplusManager:

    def calculate_surplus(self, db: Session,
                          period_start: datetime,
                          period_end: datetime) -> dict:
        """
        Calculate surplus for a period.
        Surplus = total fees collected - operating costs.
        """
        from sqlalchemy import func
        from .database import Order

        total_fees = db.query(func.sum(Order.platform_fee)).filter(
            Order.status == "completed",
            Order.created_at >= period_start,
            Order.created_at <= period_end,
        ).scalar() or 0.0

        return {
            "period_start":   period_start.isoformat(),
            "period_end":     period_end.isoformat(),
            "total_collected": total_fees,
            "note": "Operating costs are subtracted before surplus is calculated. Enter actual operating costs to determine donation amount."
        }

    def designate_donation(self, db: Session,
                           period_start: datetime,
                           period_end: datetime,
                           operating_costs: float,
                           total_collected: float,
                           cause_name: str,
                           cause_url: str,
                           cause_description: str,
                           public_note: str) -> dict:
        """
        The Architect, Founder of The Commons designates the cause and amount.
        Called every 6 months.
        """
        surplus = max(0.0, total_collected - operating_costs)

        if surplus <= 0:
            return {
                "ok":      False,
                "error":   "No surplus available for this period.",
                "surplus": surplus,
            }

        donation = SurplusDonation(
            period_start      = period_start,
            period_end        = period_end,
            operating_costs   = operating_costs,
            total_collected   = total_collected,
            surplus_amount    = surplus,
            cause_name        = cause_name,
            cause_url         = cause_url,
            cause_description = cause_description,
            public_note       = public_note,
            designated_by     = "The Architect, Founder of The Commons",
        )
        db.add(donation)
        db.commit()
        db.refresh(donation)

        print(f"[SURPLUS] Donation designated: ${surplus:.2f} to {cause_name}")
        print(f"[SURPLUS] This will be published publicly on the platform.")

        return {
            "ok":       True,
            "donation": {
                "id":             donation.id,
                "surplus":        f"${surplus:.2f}",
                "cause":          cause_name,
                "period":         f"{period_start.strftime('%B %Y')} — {period_end.strftime('%B %Y')}",
                "designated_by":  "The Architect, Founder of The Commons",
            }
        }

    def confirm_donation(self, db: Session, donation_id: int) -> dict:
        """Mark donation as confirmed — money has been sent."""
        donation = db.query(SurplusDonation).filter(
            SurplusDonation.id == donation_id
        ).first()
        if not donation:
            return {"ok": False, "error": "Donation record not found."}

        donation.confirmed   = True
        donation.donated_at  = datetime.utcnow()
        db.commit()

        print(f"[SURPLUS] Donation {donation_id} confirmed — ${donation.surplus_amount:.2f} to {donation.cause_name}")
        return {"ok": True}

    def get_public_record(self, db: Session) -> list:
        """
        Full public record of every donation ever made.
        Transparent. Always.
        """
        donations = (
            db.query(SurplusDonation)
            .order_by(SurplusDonation.period_end.desc())
            .all()
        )
        return [
            {
                "period":           f"{d.period_start.strftime('%B %Y')} — {d.period_end.strftime('%B %Y')}",
                "cause":            d.cause_name,
                "cause_url":        d.cause_url,
                "cause_description": d.cause_description,
                "amount":           f"${d.surplus_amount:.2f}",
                "total_collected":  f"${d.total_collected:.2f}",
                "operating_costs":  f"${d.operating_costs:.2f}",
                "confirmed":        d.confirmed,
                "donated_at":       d.donated_at.isoformat() if d.donated_at else "Pending",
                "designated_by":    d.designated_by,
                "public_note":      d.public_note,
            }
            for d in donations
        ]


surplus_manager = SurplusManager()
