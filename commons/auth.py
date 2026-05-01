"""
auth.py — Authentication

Username and password only.
No biometrics. No phone number required. No body data collected.
Your identity is yours.

JWT tokens for session management.
Passwords hashed with bcrypt — never stored plaintext.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db, User, UserRole
from .config import config

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

RESERVED_USERNAMES = {
    "admin", "sovereign", "circle", "commons", "moderator",
    "system", "fingerprint", "codex", "support", "help",
    "thecommons", "the_commons"
}


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=config.jwt_expire_hours)
    data   = {"sub": str(user_id), "username": username, "exp": expire}
    return jwt.encode(data, config.secret_key, algorithm=config.jwt_algorithm)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, config.secret_key, algorithms=[config.jwt_algorithm])
    except JWTError:
        return None


# ── User Creation ─────────────────────────────────────────────────────────────

def validate_username(username: str) -> dict:
    if len(username) < 3:
        return {"ok": False, "error": "Username must be at least 3 characters."}
    if len(username) > 50:
        return {"ok": False, "error": "Username must be 50 characters or fewer."}
    if not username.replace("_", "").replace("-", "").isalnum():
        return {"ok": False, "error": "Username may only contain letters, numbers, underscores, and hyphens."}
    if username.lower() in RESERVED_USERNAMES:
        return {"ok": False, "error": "That username is reserved."}
    return {"ok": True}

def validate_password(password: str) -> dict:
    if len(password) < 8:
        return {"ok": False, "error": "Password must be at least 8 characters."}
    if len(password) > 128:
        return {"ok": False, "error": "Password is too long."}
    return {"ok": True}

def register_user(db: Session, username: str, email: str,
                  password: str, display_name: str = None,
                  is_minor: bool = False) -> dict:

    # Validate username
    v = validate_username(username)
    if not v["ok"]:
        return {"ok": False, "error": v["error"]}

    # Validate password
    v = validate_password(password)
    if not v["ok"]:
        return {"ok": False, "error": v["error"]}

    # Check uniqueness
    if db.query(User).filter(User.username == username).first():
        return {"ok": False, "error": "Username already taken."}
    if db.query(User).filter(User.email == email).first():
        return {"ok": False, "error": "An account with that email already exists."}

    user = User(
        username      = username,
        email         = email,
        password_hash = hash_password(password),
        display_name  = display_name or username,
        is_minor      = is_minor,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id, user.username)
    return {"ok": True, "user": user, "token": token}


def login_user(db: Session, username: str, password: str) -> dict:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {"ok": False, "error": "Invalid username or password."}
    if not verify_password(password, user.password_hash):
        return {"ok": False, "error": "Invalid username or password."}
    if not user.is_active:
        return {"ok": False, "error": "This account is not active."}

    user.last_seen = datetime.utcnow()
    db.commit()

    token = create_token(user.id, user.username)
    return {"ok": True, "user": user, "token": token}


# ── Current User ──────────────────────────────────────────────────────────────

def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive.")
    return user

def get_current_user_optional(token: str = Depends(oauth2_scheme),
                               db: Session = Depends(get_db)) -> Optional[User]:
    try:
        return get_current_user(token, db)
    except Exception:
        return None

def require_circle(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.CIRCLE, UserRole.SOVEREIGN):
        raise HTTPException(status_code=403, detail="Circle access required.")
    return user

def require_sovereign(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.SOVEREIGN:
        raise HTTPException(status_code=403, detail="Sovereign authority required.")
    return user


def send_magic_link(db, user) -> dict:
    """
    Send a magic sign-in link to the user's email.
    TODO: wire up Gmail SMTP via GMAIL_APP_PASSWORD env var.
    """
    import os, secrets
    from datetime import datetime, timedelta

    # Generate a secure token
    token = secrets.token_urlsafe(32)

    # For now return ok=False with a friendly message until SMTP is configured
    gmail_pw = os.getenv("GMAIL_APP_PASSWORD", "")
    if not gmail_pw:
        return {"ok": False, "error": "Email sign-in is not yet configured. Please contact support."}

    # SMTP sending — fill in when Gmail app password is set
    try:
        import smtplib
        from email.mime.text import MIMEText
        gmail_from = os.getenv("GMAIL_FROM", "sentinel.commons@gmail.com")
        base_url   = os.getenv("BASE_URL", "https://the-commons.onrender.com")
        link       = f"{base_url}/auth/verify?token={token}&uid={user.id}"
        msg        = MIMEText(f"Your Commons sign-in link:\n\n{link}\n\nExpires in 15 minutes.")
        msg["Subject"] = "Your Commons Sign-In Link"
        msg["From"]    = gmail_from
        msg["To"]      = user.email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_from, gmail_pw)
            smtp.send_message(msg)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}
