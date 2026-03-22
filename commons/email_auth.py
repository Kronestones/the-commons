"""
email_auth.py — Magic Link Authentication
No passwords. No bcrypt. Just a secure link sent to email.
"""
import secrets
import requests
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from .database import get_db, User
from .config import config

# Store magic tokens in memory
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
This link expires in 15 minutes.

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
