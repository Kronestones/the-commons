"""
parental.py — Parental Controls

A parent sets a PIN. The minor's account is approved.
Content filtering kicks in automatically.

Simple. Respectful. Protective without being invasive.

No biometrics. No surveillance of the child.
Just a PIN between a parent and their child's account.

Codex Law 4: No Biometrics.
Codex Law 8: Children are protected.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

import hashlib
import secrets
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Session
from .database import Base, User


class ParentalControl(Base):
    """
    Links a minor account to a parent PIN.
    Parent sets PIN → account is approved → content filtering active.
    """
    __tablename__ = "parental_controls"

    id              = Column(Integer, primary_key=True, index=True)
    minor_user_id   = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    pin_hash        = Column(String(255), nullable=False)   # Hashed — never stored plain
    pin_salt        = Column(String(64), nullable=False)
    parent_email    = Column(String(255), default="")       # Optional — for notifications
    approved        = Column(Boolean, default=False)
    approved_at     = Column(DateTime, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)


class ParentalManager:

    def _hash_pin(self, pin: str, salt: str) -> str:
        return hashlib.sha256((salt + pin).encode()).hexdigest()

    def setup_parental_control(self, db: Session, minor_user_id: int,
                                pin: str, parent_email: str = "") -> dict:
        """
        Parent sets a PIN for a minor's account.
        Once set, the account requires PIN approval to be active.
        """
        # Validate PIN
        if len(pin) < 4:
            return {"ok": False, "error": "PIN must be at least 4 digits."}
        if len(pin) > 8:
            return {"ok": False, "error": "PIN must be 8 digits or fewer."}
        if not pin.isdigit():
            return {"ok": False, "error": "PIN must be numbers only."}

        # Check user exists and is a minor
        user = db.query(User).filter(User.id == minor_user_id).first()
        if not user:
            return {"ok": False, "error": "Account not found."}

        # Check no existing control
        existing = db.query(ParentalControl).filter(
            ParentalControl.minor_user_id == minor_user_id
        ).first()
        if existing:
            return {"ok": False, "error": "Parental control already set up for this account."}

        salt     = secrets.token_hex(32)
        pin_hash = self._hash_pin(pin, salt)

        control = ParentalControl(
            minor_user_id = minor_user_id,
            pin_hash      = pin_hash,
            pin_salt      = salt,
            parent_email  = parent_email,
            approved      = False,
        )
        db.add(control)

        # Mark user as minor
        user.is_minor = True
        db.commit()

        print(f"[PARENTAL] Parental control set up for user {minor_user_id}.")
        return {
            "ok":      True,
            "message": "Parental control set up. Use your PIN to approve the account.",
            "next":    "Call /api/parental/approve with the PIN to activate the account."
        }

    def approve_account(self, db: Session, minor_user_id: int, pin: str) -> dict:
        """
        Parent enters PIN to approve the minor's account.
        Account becomes active with content filtering enabled.
        """
        control = db.query(ParentalControl).filter(
            ParentalControl.minor_user_id == minor_user_id
        ).first()
        if not control:
            return {"ok": False, "error": "No parental control found for this account."}

        pin_hash = self._hash_pin(pin, control.pin_salt)
        if pin_hash != control.pin_hash:
            return {"ok": False, "error": "Incorrect PIN."}

        control.approved    = True
        control.approved_at = datetime.utcnow()
        db.commit()

        print(f"[PARENTAL] Account {minor_user_id} approved by parent PIN.")
        return {
            "ok":      True,
            "message": "Account approved. Content filtering is now active.",
            "protections": [
                "Political content filtered from feed",
                "Cannot comment on political posts",
                "Cannot share political content",
                "Community value filter active",
                "Age-appropriate content only"
            ]
        }

    def change_pin(self, db: Session, minor_user_id: int,
                   old_pin: str, new_pin: str) -> dict:
        """Parent changes their PIN."""
        control = db.query(ParentalControl).filter(
            ParentalControl.minor_user_id == minor_user_id
        ).first()
        if not control:
            return {"ok": False, "error": "No parental control found."}

        old_hash = self._hash_pin(old_pin, control.pin_salt)
        if old_hash != control.pin_hash:
            return {"ok": False, "error": "Incorrect current PIN."}

        if len(new_pin) < 4 or not new_pin.isdigit():
            return {"ok": False, "error": "New PIN must be at least 4 digits."}

        new_salt = secrets.token_hex(32)
        control.pin_hash = self._hash_pin(new_pin, new_salt)
        control.pin_salt = new_salt
        db.commit()

        return {"ok": True, "message": "PIN updated successfully."}

    def remove_parental_control(self, db: Session, minor_user_id: int,
                                 pin: str) -> dict:
        """Parent removes parental control with PIN verification."""
        control = db.query(ParentalControl).filter(
            ParentalControl.minor_user_id == minor_user_id
        ).first()
        if not control:
            return {"ok": False, "error": "No parental control found."}

        pin_hash = self._hash_pin(pin, control.pin_salt)
        if pin_hash != control.pin_hash:
            return {"ok": False, "error": "Incorrect PIN."}

        db.delete(control)
        db.commit()
        return {"ok": True, "message": "Parental control removed."}

    def is_approved(self, db: Session, minor_user_id: int) -> bool:
        """Check if a minor account has been approved by a parent."""
        control = db.query(ParentalControl).filter(
            ParentalControl.minor_user_id == minor_user_id
        ).first()
        if not control:
            return True   # No parental control set — account is active
        return control.approved

    def get_status(self, db: Session, minor_user_id: int) -> dict:
        """Get parental control status for an account."""
        control = db.query(ParentalControl).filter(
            ParentalControl.minor_user_id == minor_user_id
        ).first()
        if not control:
            return {"has_parental_control": False}
        return {
            "has_parental_control": True,
            "approved":             control.approved,
            "approved_at":          control.approved_at.isoformat() if control.approved_at else None,
            "protections_active":   control.approved,
        }


parental = ParentalManager()
