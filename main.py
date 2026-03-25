"""
main.py — The Commons

The launcher. Wires everything. Opens the platform.

Usage:
    python main.py              # Start The Commons
    python main.py --check      # Check configuration
    python main.py --dev        # Development mode

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

import argparse
import sys
import os
import uvicorn
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Session, relationship

# ── Parse args ────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="The Commons — A public platform for the people")
parser.add_argument("--check",   action="store_true", help="Check configuration and exit")
parser.add_argument("--dev",     action="store_true", help="Development mode")
parser.add_argument("--version", action="store_true", help="Print version and exit")
args = parser.parse_args()

VERSION = "0.1.0"

if args.version:
    print(f"The Commons v{VERSION}")
    sys.exit(0)

# ── Imports ───────────────────────────────────────────────────────────────────

from commons.email_auth import generate_magic_token, verify_magic_token, send_magic_link, MagicToken
from commons.config     import config
from commons.database   import init_db, get_db, User, Post, PostStatus, Base, engine
from commons.codex      import TheCommonsCodex
from commons.auth       import (register_user, login_user, get_current_user,
                                get_current_user_optional, create_token)
from commons.posts      import posts
from commons.circle     import circle
from commons.fingerprint    import fingerprint
from commons.commerce       import commerce
from commons.resilience     import heartbeat, revival
from commons.preferences    import preference_engine, WatchEvent
from commons.surplus        import surplus_manager
from commons.security       import (
    SecurityHeadersMiddleware, RequestSizeLimitMiddleware,
    RateLimitMiddleware, rate_limiter, sanitizer, get_client_ip,
    enforce_rate_limit
)

# ── Vote model ────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, ForeignKey

class Vote(Base):
    __tablename__ = "votes"
    id      = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    value   = Column(Integer, nullable=False)
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="one_vote_per_post"),
    )

# ── Check ─────────────────────────────────────────────────────────────────────

if args.check:
    config.print_status()
    sys.exit(0 if config.is_ready() else 1)

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "The Commons",
    description = "A public platform for the people. Power to the People.",
    version     = VERSION,
    docs_url    = "/api/docs" if config.debug else None,
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RateLimitMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media",  StaticFiles(directory=str(config.media_dir)), name="media")
templates = Jinja2Templates(directory="templates")

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    revival.startup_check()
    init_db()
    Base.metadata.create_all(bind=engine)
    heartbeat.start()
    from commons.preferences import (UserTopicPreference, UserCreatorAffinity,
                                      UserContentTypePreference, WatchEvent)
    Base.metadata.create_all(bind=engine)
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║              T H E   C O M M O N S                  ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Version:  {VERSION:<43}║")
    print(f"║  Host:     {config.host}:{config.port:<38}║")
    print(f"║  Mode:     {'Production':<43}║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Sovereign Human T.L. Powers                         ║")
    print("║  Power to the People                                 ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

@app.on_event("shutdown")
async def shutdown():
    heartbeat.stop()
    print("[THE COMMONS] Clean shutdown. The platform is pausing — not ending.")

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_current_user_from_cookie(request: Request, db: Session):
    token = request.cookies.get("token")
    if not token:
        return None
    try:
        return get_current_user(db=db, token=token)
    except Exception:
        return None

def attach_vote_data(posts_list, current_user, db):
    for p in posts_list:
        ups   = db.query(Vote).filter_by(post_id=p.id, value=1).count()
        downs = db.query(Vote).filter_by(post_id=p.id, value=-1).count()
        p.vote_score = ups - downs
        p.up_count   = ups
        p.down_count = downs
        if current_user:
            v = db.query(Vote).filter_by(post_id=p.id, user_id=current_user.id).first()
            p.user_voted = v.value if v else 0
        else:
            p.user_voted = 0
    return posts_list

# ── Pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    if current_user:
        return RedirectResponse("/feed", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"version": VERSION, "current_user": None}
    )

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(request=request, name="register.html", context={"current_user": current_user})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(request=request, name="login.html", context={"current_user": current_user})

@app.get("/codex", response_class=HTMLResponse)
async def codex_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(
        request=request,
        name="codex.html",
        context={"codex": TheCommonsCodex, "sources": fingerprint.get_verified_sources(), "current_user": current_user}
    )

@app.get("/feed", response_class=HTMLResponse)
async def feed_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    feed_posts = (
        db.query(Post)
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(Post.published_at.desc())
        .limit(50)
        .all()
    )
    attach_vote_data(feed_posts, current_user, db)
    return templates.TemplateResponse(
        request=request,
        name="feed.html",
        context={"posts": feed_posts, "current_user": current_user}
    )

@app.get("/profile/edit", response_class=HTMLResponse)
async def profile_edit_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request=request, name="profile_edit.html", context={"current_user": current_user})

@app.post("/profile/edit", response_class=HTMLResponse)
async def profile_edit_save(
    request:    Request,
    username:   str = Form(...),
    bio:        str = Form(default=""),
    avatar_url: str = Form(default=""),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    bio        = bio.strip()[:300]
    avatar_url = avatar_url.strip()[:500]
    new_username = username.strip()
    if new_username and new_username != current_user.username:
        clash = db.query(User).filter(User.username == new_username).first()
        if clash:
            return templates.TemplateResponse(
                request=request,
                name="profile_edit.html",
                context={"current_user": current_user, "error": "That username is already taken."}
            )
        current_user.username = new_username
    current_user.bio        = bio
    current_user.avatar_url = avatar_url
    db.commit()
    return RedirectResponse(f"/profile/{current_user.username}", status_code=302)

@app.get("/profile/{username}", response_class=HTMLResponse)
async def profile_page(username: str, request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    profile_user = db.query(User).filter(User.username == username).first()
    if not profile_user:
        return HTMLResponse("<h2>User not found.</h2>", status_code=404)
    user_posts = (
        db.query(Post)
        .filter(Post.author_id == profile_user.id)
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(Post.published_at.desc())
        .limit(50)
        .all()
    )
    attach_vote_data(user_posts, current_user, db)
    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "profile_user": profile_user,
            "posts":        user_posts,
            "current_user": current_user,
            "is_own":       current_user and current_user.id == profile_user.id,
        }
    )

@app.get("/marketplace", response_class=HTMLResponse)
async def marketplace_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    return templates.TemplateResponse(request=request, name="marketplace.html", context={"current_user": current_user})

@app.get("/giving", response_class=HTMLResponse)
async def giving_page(request: Request, db: Session = Depends(get_db)):
    current_user = get_current_user_from_cookie(request, db)
    record = surplus_manager.get_public_record(db)
    return templates.TemplateResponse(
        request=request,
        name="giving.html",
        context={"donations": record, "codex": TheCommonsCodex, "current_user": current_user}
    )

# ── Voting ────────────────────────────────────────────────────────────────────

@app.post("/post/{post_id}/vote", response_class=HTMLResponse)
async def vote_on_post(
    post_id: int,
    request: Request,
    value:   int = Form(...),
    db: Session = Depends(get_db)
):
    current_user = get_current_user_from_cookie(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return HTMLResponse("Post not found", status_code=404)
    existing = db.query(Vote).filter_by(post_id=post_id, user_id=current_user.id).first()
    if existing:
        if existing.value == value:
            db.delete(existing)
        else:
            existing.value = value
    else:
        db.add(Vote(post_id=post_id, user_id=current_user.id, value=value))
    db.commit()
    referer = request.headers.get("referer", "/feed")
    return RedirectResponse(referer, status_code=302)

# ── Logout ────────────────────────────────────────────────────────────────────

@app.get("/logout")
async def logout():
    response = RedirectResponse("/", status_code=302)
    response.delete_cookie("token")
    response.delete_cookie("username")
    return response

# ── Auth API ──────────────────────────────────────────────────────────────────

@app.post("/auth/register")
async def api_register(
    request:      Request,
    username:     str  = Form(...),
    email:        str  = Form(...),
    password:     str  = Form(default=""),
    display_name: str  = Form(default=""),
    is_minor:     bool = Form(default=False),
    db: Session = Depends(get_db)
):
    try:
        ip = get_client_ip(request)
        enforce_rate_limit(ip, "register")
    except Exception:
        pass
    u = sanitizer.sanitize_username(username)
    if not u["ok"]:
        return JSONResponse({"ok": False, "error": u["error"]}, status_code=400)
    e = sanitizer.sanitize_email(email)
    if not e["ok"]:
        return JSONResponse({"ok": False, "error": e["error"]}, status_code=400)
    d = sanitizer.sanitize_text(display_name or username, max_length=100)
    if not d["ok"]:
        return JSONResponse({"ok": False, "error": d["error"]}, status_code=400)
    try:
        result = register_user(db, u["value"], e["value"], "", d["value"], is_minor)
        if not result["ok"]:
            return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
        token = generate_magic_token(e["value"], db)
        send_magic_link(e["value"], token)
        return JSONResponse({
            "ok":    True,
            "token": result["token"],
            "user":  {"id": result["user"].id, "username": result["user"].username}
        })
    except Exception as ex:
        return JSONResponse({"ok": False, "error": f"Registration failed: {str(ex)}"}, status_code=500)

@app.post("/auth/login")
async def api_login(
    request:  Request,
    username: str = Form(...),
    password: str = Form(default=""),
    db: Session = Depends(get_db)
):
    try:
        ip = get_client_ip(request)
        enforce_rate_limit(ip, "login")
    except Exception:
        pass
    u = sanitizer.sanitize_username(username)
    if not u["ok"]:
        return JSONResponse({"ok": False, "error": u["error"]}, status_code=400)
    result = login_user(db, u["value"], password)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=401)
    rate_limiter.clear_cooldown(ip, "login")
    return JSONResponse({
        "ok":    True,
        "token": result["token"],
        "user":  {"id": result["user"].id, "username": result["user"].username}
    })

@app.post("/auth/magic/request")
async def request_magic_link(
    request: Request,
    email:   str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        return JSONResponse({"ok": False, "error": "No account with that email."}, status_code=400)
    token = generate_magic_token(email.lower().strip(), db)
    sent  = send_magic_link(email.lower().strip(), token)
    if not sent:
        return JSONResponse({"ok": False, "error": "Failed to send email. Please try again."}, status_code=500)
    return JSONResponse({"ok": True, "message": "Check your email for a sign-in link."})

@app.get("/auth/magic")
async def verify_magic_link(token: str, db: Session = Depends(get_db)):
    try:
        email = verify_magic_token(token, db)
        if not email:
            return HTMLResponse("<h2>This link has expired or is invalid. Please request a new one.</h2>")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return HTMLResponse("<h2>Account not found.</h2>")
        jwt_token = create_token(user.id, user.username)
        response = RedirectResponse(url="/feed")
        response.set_cookie("token",    jwt_token,     httponly=False, max_age=60*60*24*30)
        response.set_cookie("username", user.username, httponly=False, max_age=60*60*24*30)
        return response
    except Exception as e:
        return HTMLResponse(f"<h2>Error: {str(e)}</h2>")

# ── Posts API ─────────────────────────────────────────────────────────────────

@app.post("/api/posts")
async def api_create_post(
    request:      Request,
    content:      str  = Form(default=""),
    post_type:    str  = Form(default="text"),
    is_news:      bool = Form(default=False),
    is_political: bool = Form(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    enforce_rate_limit(ip, "post")
    c = sanitizer.sanitize_text(content, max_length=10000)
    if not c["ok"]:
        return JSONResponse({"ok": False, "error": c["error"]}, status_code=400)
    allowed_types = {"text", "image", "video", "audio", "live"}
    if post_type not in allowed_types:
        return JSONResponse({"ok": False, "error": "Invalid post type."}, status_code=400)
    result = posts.create(db, current_user, post_type, content=c["value"], is_news=is_news, is_political=is_political)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
    post = result["post"]
    return JSONResponse({
        "ok":      True,
        "post_id": post.id,
        "status":  post.status.value,
        "message": (
            "Your post is live." if post.status == PostStatus.PUBLISHED
            else "Your post is being verified and will appear shortly."
        )
    })

@app.get("/api/feed")
async def api_feed(
    limit:  int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = posts.get_feed(db, current_user, limit, offset)
    feed = []
    for post in result["posts"]:
        feed.append({
            "id":              post.id,
            "author":          post.author.username if post.author else "unknown",
            "content":         post.content,
            "post_type":       post.post_type.value,
            "community_score": post.community_score,
            "view_count":      post.view_count,
            "published_at":    post.published_at.isoformat() if post.published_at else None,
            "reason":          posts.get_feed_reason(post, current_user),
        })
    return JSONResponse({"ok": True, "feed": feed, "mode": result["mode"].value})

@app.post("/api/posts/{post_id}/vote")
async def api_vote(
    post_id: int,
    value:   int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = posts.cast_community_vote(db, current_user, post_id, value)
    return JSONResponse(result)

# ── Fingerprint API ───────────────────────────────────────────────────────────

@app.get("/api/fingerprint/pending")
async def api_fingerprint_pending(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required")
    count = fingerprint.pending_review_count(db)
    held  = db.query(Post).filter(Post.status == PostStatus.HELD).limit(50).all()
    return JSONResponse({
        "ok": True,
        "pending_count": count,
        "posts": [{"id": p.id, "content": p.content[:200], "author": p.author.username} for p in held]
    })

@app.post("/api/fingerprint/review/{post_id}")
async def api_fingerprint_review(
    post_id:  int,
    decision: str = Form(...),
    reason:   str = Form(...),
    notes:    str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required")
    result = fingerprint.human_review(db, post_id, current_user.username, decision, reason, notes)
    return JSONResponse(result)

# ── Circle API ────────────────────────────────────────────────────────────────

@app.post("/api/circle/appeal/{post_id}")
async def api_appeal(
    post_id: int,
    reason:  str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post or post.author_id != current_user.id:
        raise HTTPException(403, "You can only appeal your own posts.")
    result = circle.open_appeal(db, post_id, reason)
    return JSONResponse(result)

@app.get("/api/codex")
async def api_codex():
    return JSONResponse({
        "ok":        True,
        "platform":  TheCommonsCodex.PLATFORM,
        "spirit":    TheCommonsCodex.SPIRIT,
        "sovereign": TheCommonsCodex.SOVEREIGN,
        "laws":      TheCommonsCodex.LAWS,
        "sources":   fingerprint.get_verified_sources(),
    })

# ── Preference API ────────────────────────────────────────────────────────────

@app.get("/api/preferences")
async def api_get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = preference_engine.get_profile(db, current_user.id)
    return JSONResponse({
        "ok":      True,
        "profile": profile,
        "note":    "This is everything The Commons uses to personalize your feed. You can reset it anytime."
    })

@app.post("/api/preferences/reset")
async def api_reset_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = preference_engine.reset_preferences(db, current_user.id)
    return JSONResponse(result)

@app.post("/api/posts/{post_id}/watch")
async def api_record_watch(
    post_id:       int,
    watch_percent: float = Form(...),
    current_user:  User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found")
    engagement = "complete" if watch_percent >= 90 else "view" if watch_percent > 10 else "skip"
    preference_engine.record_engagement(db, current_user.id, post, engagement, watch_percent)
    return JSONResponse({"ok": True})

@app.get("/api/feed/personalized")
async def api_personalized_feed(
    limit:  int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    results = preference_engine.get_personalized_feed(db, current_user, limit, offset)
    feed = []
    for item in results:
        post = item["post"]
        feed.append({
            "id":              post.id,
            "author":          post.author.username if post.author else "unknown",
            "content":         post.content,
            "post_type":       post.post_type.value,
            "community_score": post.community_score,
            "view_count":      post.view_count,
            "published_at":    post.published_at.isoformat() if post.published_at else None,
            "reason":          item["reason"],
            "score":           round(item["score"], 2),
        })
    return JSONResponse({"ok": True, "feed": feed, "mode": "personalized"})

# ── Giving API ────────────────────────────────────────────────────────────────

@app.get("/api/giving")
async def api_giving(db: Session = Depends(get_db)):
    return JSONResponse({
        "ok":        True,
        "donations": surplus_manager.get_public_record(db),
        "note":      "Codex Law 17 — surplus donated every 6 months. Full transparency always."
    })

@app.post("/api/giving/designate")
async def api_designate_donation(
    period_start:      str   = Form(...),
    period_end:        str   = Form(...),
    operating_costs:   float = Form(...),
    total_collected:   float = Form(...),
    cause_name:        str   = Form(...),
    cause_url:         str   = Form(default=""),
    cause_description: str   = Form(default=""),
    public_note:       str   = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required. Codex Law 17.")
    from datetime import datetime
    result = surplus_manager.designate_donation(
        db,
        datetime.fromisoformat(period_start),
        datetime.fromisoformat(period_end),
        operating_costs, total_collected,
        cause_name, cause_url, cause_description, public_note,
    )
    return JSONResponse(result)

@app.post("/api/giving/confirm/{donation_id}")
async def api_confirm_donation(
    donation_id:  int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required.")
    result = surplus_manager.confirm_donation(db, donation_id)
    return JSONResponse(result)

# ── Marketplace API ───────────────────────────────────────────────────────────

@app.get("/api/marketplace")
async def api_marketplace(limit: int = 40, offset: int = 0, db: Session = Depends(get_db)):
    products = commerce.get_marketplace(db, limit, offset)
    result = []
    for p in products:
        from commons.database import SellerProfile
        seller = db.query(SellerProfile).filter_by(id=p.seller_id).first()
        seller_user = db.query(User).filter_by(id=seller.user_id).first() if seller else None
        result.append({
            "id":              p.id,
            "name":            p.name,
            "description":     p.description,
            "price":           p.price,
            "media_path":      p.media_path,
            "community_score": p.community_score,
            "seller":          seller_user.username if seller_user else "unknown",
            "business_type":   seller.business_type if seller else "unknown",
        })
    return JSONResponse({"ok": True, "products": result})

@app.get("/api/marketplace/{product_id}")
async def api_get_product(product_id: int, db: Session = Depends(get_db)):
    product = commerce.get_product(db, product_id)
    if not product:
        raise HTTPException(404, "Product not found")
    from commons.database import SellerProfile
    seller = db.query(SellerProfile).filter_by(id=product.seller_id).first()
    seller_user = db.query(User).filter_by(id=seller.user_id).first() if seller else None
    return JSONResponse({"ok": True, "product": {
        "id":            product.id,
        "name":          product.name,
        "description":   product.description,
        "price":         product.price,
        "media_path":    product.media_path,
        "seller":        seller_user.username if seller_user else "unknown",
        "business_type": seller.business_type if seller else "unknown",
    }})

@app.post("/api/marketplace/products")
async def api_list_product(
    request:     Request,
    name:        str   = Form(...),
    description: str   = Form(default=""),
    price:       float = Form(...),
    photo:       UploadFile = File(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    media_path = None
    if photo and photo.filename:
        import shutil, uuid
        ext = photo.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        dest = config.media_dir / filename
        with open(dest, "wb") as f:
            shutil.copyfileobj(photo.file, f)
        media_path = filename
    result = commerce.create_product(db, current_user, name, description, price, media_path=media_path)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
    return JSONResponse({"ok": True, "product_id": result["product"].id})

@app.post("/api/marketplace/purchase")
async def api_purchase(
    product_ids:  str  = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        ids = [int(x.strip()) for x in product_ids.split(",") if x.strip()]
    except ValueError:
        return JSONResponse({"ok": False, "error": "Invalid product IDs."}, status_code=400)
    result = commerce.initiate_purchase(db, current_user, ids)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
    return JSONResponse({"ok": True, "breakdown": result["breakdown"], "order_id": result["order"].id})

@app.post("/api/marketplace/seller/register")
async def api_register_seller(
    business_name: str = Form(...),
    business_type: str = Form(...),
    current_user:  User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = commerce.register_seller(db, current_user, business_name, business_type)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
    return JSONResponse({"ok": True})

@app.get("/api/marketplace/stats/platform")
async def api_platform_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required")
    return JSONResponse(commerce.platform_stats(db))

@app.post("/api/user/algorithm-mode")
async def api_set_algorithm_mode(
    mode: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.database import AlgorithmMode
    try:
        current_user.algorithm_mode = AlgorithmMode(mode)
        db.commit()
        return JSONResponse({"ok": True, "mode": mode})
    except ValueError:
        return JSONResponse({"ok": False, "error": "Invalid mode."}, status_code=400)

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "platform": "The Commons", "spirit": "Power to the People"}

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host    = config.host,
        port    = config.port,
        reload  = config.debug,
        workers = 1 if config.debug else 4,
    )
