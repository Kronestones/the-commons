"""
magic_routes.py — Magic Link Routes
"""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .database import get_db, User
from .auth import create_token
from .email_auth import generate_magic_token, verify_magic_token, send_magic_link

router = APIRouter()

@router.post("/auth/magic/request")
async def request_magic_link(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"ok": False, "error": "No account with that email."}
    token = generate_magic_token(email)
    sent = send_magic_link(email, token)
    if not sent:
        return {"ok": False, "error": "Failed to send email. Please try again."}
    return {"ok": True, "message": "Check your email for a sign-in link."}

@router.get("/auth/magic")
async def verify_magic_link(token: str, db: Session = Depends(get_db)):
    email = verify_magic_token(token)
    if not email:
        return HTMLResponse("<h2>This link has expired or is invalid. Please request a new one.</h2>")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return HTMLResponse("<h2>Account not found.</h2>")
    jwt_token = create_token(user.id, user.username)
    response = RedirectResponse(url="/feed")
    response.set_cookie("token", jwt_token, httponly=True, max_age=60*60*24*30)
    return response
