"""
email_auth.py — Magic Link Authentication
No passwords. No bcrypt. Just a secure link sent to email.
"""
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import get_db, User
from .config import config

# Store magic tokens in memory (simple for now)
magic_tokens = {}

def generate_magic_token(email: str) -> str:
    token = secrets.token_urlsafe(32)
    magic_tokens[token] = {
        "email": email,
        "expires": datetime.utcnow() + timedelta(minutes=15)
    }
    return token

def verify_magic_token(token: str) -> str | None:
    data = magic_tokens.get(token)
    if not data:
        return None
    if datetime.utcnow() > data["expires"]:
        del magic_tokens[token]
        return None
    del magic_tokens[token]
    return data["email"]

def send_magic_link(email: str, token: str) -> bool:
    link = f"{config.base_url}/auth/magic?token={token}"
    try:
        msg = MIMEMultipart()
        msg["From"] = config.email_user
        msg["To"] = email
        msg["Subject"] = "Your sign-in link for The Commons"
        body = f"""
Hello,

Click the link below to sign in to The Commons.
This link expires in 15 minutes.

{link}

If you didn't request this, ignore this email.

Power to the People.
— The Commons
        """
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(config.email_host, config.email_port) as server:
            server.starttls()
            server.login(config.email_user, config.email_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")
        return False
