"""
magic_routes.py — Magic Link Routes
"""
from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from .database import get_db, User
from .auth import create_token
from .email_auth import generate_magic_token, verify_magic_token, send_magic_link

router = APIRouter()


@router.post("/auth/magic/request")
async def request_magic_link(
    email: str = Form(...),
    db:    Session = Depends(get_db)
):
    # Check recovery emails or regular email
    from sqlalchemy import text
    recovery = db.execute(
        text("SELECT user_id FROM sovereign_recovery_emails WHERE LOWER(email) = LOWER(:e)"),
        {"e": email}
    ).fetchone()

    if recovery:
        user = db.query(User).filter(User.id == recovery.user_id).first()
    else:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        return {"ok": True, "message": "Check your email for a sign-in link."}

    token = generate_magic_token(email, db)
    sent  = send_magic_link(email, token)
    if not sent:
        return {"ok": False, "error": "Failed to send email. Please try again."}
    return {"ok": True, "message": "Check your email for a sign-in link."}


@router.get("/auth/magic")
async def verify_magic_link(token: str, db: Session = Depends(get_db)):
    email = verify_magic_token(token, db)
    if not email:
        return HTMLResponse("<h2>This link has expired or is invalid. Please request a new one.</h2>")

    from sqlalchemy import text
    recovery = db.execute(
        text("SELECT user_id FROM sovereign_recovery_emails WHERE LOWER(email) = LOWER(:e)"),
        {"e": email}
    ).fetchone()

    if recovery:
        user = db.query(User).filter(User.id == recovery.user_id).first()
    else:
        user = db.query(User).filter(User.email == email).first()

    if not user:
        return HTMLResponse("<h2>Account not found.</h2>")

    jwt_token = create_token(user.id, user.username)
    username  = user.username

    html = (
        "<!DOCTYPE html><html><head><title>Signing in...</title></head><body><script>"
        "localStorage.setItem('token','" + jwt_token + "');"
        "localStorage.setItem('username','" + username + "');"
        "window.location.href='/';"
        "</script><p>Signing you in...</p></body></html>"
    )
    return HTMLResponse(html)
