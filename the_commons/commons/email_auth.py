"""
email_auth.py — Magic Link Authentication
No passwords. No bcrypt. Just a secure link sent to email.
"""
import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import get_db, MagicToken
from .config import config
import resend

def generate_magic_token(email: str, db: Session) -> str:
    token = secrets.token_urlsafe(32)
    db.add(MagicToken(
        token      = token,
        email      = email,
        expires_at = datetime.utcnow() + timedelta(minutes=15)
    ))
    db.commit()
    return token

def verify_magic_token(token: str, db: Session) -> str | None:
    row = db.query(MagicToken).filter(
        MagicToken.token == token,
        MagicToken.used  == False
    ).first()
    if not row:
        return None
    if datetime.utcnow() > row.expires_at:
        db.delete(row)
        db.commit()
        return None
    row.used = True
    db.commit()
    return row.email

def send_magic_link(email: str, token: str) -> bool:
    link = f"{config.base_url}/auth/magic?token={token}"
    try:
        resend.api_key = config.resend_api_key
        resend.Emails.send({
            "from": "The Commons <noreply@thecommons.app>",
            "to": email,
            "subject": "Your sign-in link for The Commons",
            "text": f"""Hello,

Click the link below to sign in to The Commons.
This link expires in 15 minutes.

{link}

If you didn't request this, ignore this email.

Power to the People.
— The Commons"""
        })
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")
        return False
