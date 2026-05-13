"""
email_auth.py — Magic Link Authentication
No passwords. No bcrypt. Just a secure link sent to email.
"""
import secrets
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import get_db, User, Base
from sqlalchemy import Column, String, DateTime
from .config import config


class MagicToken(Base):
    __tablename__ = "magic_tokens"
    token   = Column(String, primary_key=True)
    email   = Column(String, nullable=False)
    expires = Column(DateTime, nullable=False)


def generate_magic_token(email: str, db: Session) -> str:
    token = secrets.token_urlsafe(32)
    mt = MagicToken(
        token=token,
        email=email,
        expires=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(mt)
    db.commit()
    return token


def verify_magic_token(token: str, db: Session) -> str | None:
    mt = db.query(MagicToken).filter(MagicToken.token == token).first()
    if not mt:
        return None
    if datetime.utcnow() > mt.expires:
        db.delete(mt)
        db.commit()
        return None
    email = mt.email
    db.delete(mt)
    db.commit()
    return email


def send_magic_link(email: str, token: str) -> bool:
    link = f"{config.base_url}/auth/magic?token={token}"
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {config.resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "The Commons <onboarding@resend.dev>",
                "to": [email],
                "subject": "Your sign-in link for The Commons",
                "text": f"""Hello,

Click the link below to sign in to The Commons.
This link expires in 24 hours.

{link}

If you didn't request this, ignore this email.

Power to the People.
— The Commons"""
            }
        )
        if response.status_code == 200:
            return True
        print(f"[EMAIL] Resend error: {response.text}")
        return False
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")
        return False
