"""
transparency.py — The Commons Operating Costs Transparency

Every dollar that comes in. Every dollar that goes out.
Published monthly. Always public. No exceptions.

This is not just good practice — it's Codex Law 5.
Transparency is not optional on The Commons.

Operating costs may include:
  - Render hosting fees
  - Domain registration
  - Payment processing infrastructure
  - Mobile data and device (Sovereign Human T.L. Powers
    hosts Sentinel Sanctuary on personal hardware —
    this is a real and legitimate operating cost)
  - Any other infrastructure costs

What is never an operating cost:
  - Salaries or profit distributions
  - Advertising
  - Anything that benefits shareholders
    (there are no shareholders)

Codex Law 5: Transparency.
Codex Law 12: No profit.
Codex Law 17: Surplus to the World.

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.orm import Session
from .database import Base


class OperatingCostEntry(Base):
    """
    A single operating cost entry.
    Every cost is logged, categorized, and published publicly.
    """
    __tablename__ = "operating_costs"

    id              = Column(Integer, primary_key=True, index=True)
    month           = Column(String(7), nullable=False)   # "2026-03"
    category        = Column(String(100), nullable=False)
    description     = Column(Text, nullable=False)
    amount_usd      = Column(Float, nullable=False)
    is_recurring    = Column(Boolean, default=False)
    recorded_at     = Column(DateTime, default=datetime.utcnow)
    recorded_by     = Column(String(100), default="Sovereign Human T.L. Powers")


class MonthlyReport(Base):
    """
    Published monthly transparency report.
    Total fees collected vs total costs vs surplus.
    """
    __tablename__ = "monthly_reports"

    id                  = Column(Integer, primary_key=True, index=True)
    month               = Column(String(7), unique=True, nullable=False)
    total_fees_collected = Column(Float, default=0.0)
    total_costs         = Column(Float, default=0.0)
    surplus             = Column(Float, default=0.0)
    notes               = Column(Text, default="")
    published           = Column(Boolean, default=False)
    published_at        = Column(DateTime, nullable=True)


# ── Standard Cost Categories ──────────────────────────────────────────────────

COST_CATEGORIES = [
    "Hosting — Render",
    "Domain registration",
    "Payment processing infrastructure",
    "Mobile data and device — personal hardware hosting Sentinel",
    "SSL certificate",
    "Email service",
    "Other infrastructure",
]


class TransparencyManager:

    def add_cost(self, db: Session,
                 month: str,
                 category: str,
                 description: str,
                 amount_usd: float,
                 is_recurring: bool = False) -> dict:
        """Add an operating cost entry."""
        entry = OperatingCostEntry(
            month        = month,
            category     = category,
            description  = description,
            amount_usd   = amount_usd,
            is_recurring = is_recurring,
        )
        db.add(entry)
        db.commit()
        return {"ok": True, "entry_id": entry.id}

    def publish_monthly_report(self, db: Session,
                               month: str,
                               total_fees: float,
                               notes: str = "") -> dict:
        """Publish the monthly transparency report."""
        costs = db.query(OperatingCostEntry).filter(
            OperatingCostEntry.month == month
        ).all()

        total_costs = sum(c.amount_usd for c in costs)
        surplus     = max(0.0, total_fees - total_costs)

        existing = db.query(MonthlyReport).filter(
            MonthlyReport.month == month
        ).first()

        if existing:
            existing.total_fees_collected = total_fees
            existing.total_costs          = total_costs
            existing.surplus              = surplus
            existing.notes                = notes
            existing.published            = True
            existing.published_at         = datetime.utcnow()
        else:
            db.add(MonthlyReport(
                month                = month,
                total_fees_collected = total_fees,
                total_costs          = total_costs,
                surplus              = surplus,
                notes                = notes,
                published            = True,
                published_at         = datetime.utcnow(),
            ))
        db.commit()
        return {"ok": True, "month": month, "surplus": surplus}

    def get_public_reports(self, db: Session) -> list:
        """Get all published monthly reports."""
        reports = db.query(MonthlyReport).filter(
            MonthlyReport.published == True
        ).order_by(MonthlyReport.month.desc()).all()

        result = []
        for r in reports:
            costs = db.query(OperatingCostEntry).filter(
                OperatingCostEntry.month == r.month
            ).all()

            result.append({
                "month":               r.month,
                "total_fees_collected": f"${r.total_fees_collected:.2f}",
                "total_costs":         f"${r.total_costs:.2f}",
                "surplus":             f"${r.surplus:.2f}",
                "notes":               r.notes,
                "published_at":        r.published_at.strftime("%B %d, %Y") if r.published_at else "",
                "cost_breakdown": [
                    {
                        "category":    c.category,
                        "description": c.description,
                        "amount":      f"${c.amount_usd:.2f}",
                        "recurring":   c.is_recurring,
                    }
                    for c in costs
                ]
            })
        return result

    def get_cost_categories(self) -> list:
        return COST_CATEGORIES


transparency_manager = TransparencyManager()
