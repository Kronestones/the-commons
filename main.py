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
from sqlalchemy.orm import Session

# ── Parse args ────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="The Commons — A public platform for the people")
parser.add_argument("--check", action="store_true", help="Check configuration and exit")
parser.add_argument("--dev",   action="store_true", help="Development mode")
parser.add_argument("--version", action="store_true", help="Print version and exit")
args = parser.parse_args()

VERSION = "0.1.0"

if args.version:
    print(f"The Commons v{VERSION}")
    sys.exit(0)

# ── Imports ───────────────────────────────────────────────────────────────────

from commons.email_auth import generate_magic_token, verify_magic_token, send_magic_link, MagicToken
from commons.config   import config
from commons.database import init_db, get_db, User, Post, PostStatus
from commons.codex    import TheCommonsCodex
from commons.auth     import (register_user, login_user, get_current_user,
                               get_current_user_optional, create_token)
from commons.posts    import posts
from commons.circle   import circle
from commons.fingerprint import fingerprint
from commons.commerce    import commerce
from commons.resilience  import heartbeat, revival
from commons.preferences import preference_engine, WatchEvent
from commons.surplus     import surplus_manager
from commons.security    import (
    SecurityHeadersMiddleware, RequestSizeLimitMiddleware,
    RateLimitMiddleware, rate_limiter, sanitizer, get_client_ip,
    enforce_rate_limit
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

# ── Security Middleware ───────────────────────────────────────────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(RateLimitMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media",  StaticFiles(directory=str(config.media_dir)), name="media")
templates = Jinja2Templates(directory="templates")

# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    # Revival check — detects unclean shutdown, runs recovery
    revival.startup_check()

    init_db()

    # Start heartbeat — writes pulse every 30s so we know if we crash
    heartbeat.start()

    # Register preference tables
    from commons.preferences import UserTopicPreference, UserCreatorAffinity, UserContentTypePreference, WatchEvent
    from commons.database import Base, engine
    Base.metadata.create_all(bind=engine)

    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║              T H E   C O M M O N S                  ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Version:  {VERSION:<43}║")
    print(f"║  Host:     {config.host}:{config.port:<38}║")
    print(f"║  Mode:     {'Development' if config.debug else 'Production':<43}║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Sovereign Human T.L. Powers                         ║")
    print("║  Power to the People                                 ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

@app.on_event("shutdown")
async def shutdown():
    # Write clean shutdown marker so watchdog knows this was intentional
    heartbeat.stop()
    print("[THE COMMONS] Clean shutdown. The platform is pausing — not ending.")

# ── Pages ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    # Get recent published posts for the landing feed
    recent_posts = (
        db.query(Post)
        .filter(Post.status == PostStatus.PUBLISHED)
        .order_by(Post.published_at.desc())
        .limit(20)
        .all()
    )
    return templates.TemplateResponse("index.html", {
        "request": request,
        "posts":   recent_posts,
        "version": VERSION,
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/codex", response_class=HTMLResponse)
async def codex_page(request: Request):
    return templates.TemplateResponse("codex.html", {
        "request": request,
        "codex":   TheCommonsCodex,
        "sources": fingerprint.get_verified_sources(),
    })

@app.get("/marketplace", response_class=HTMLResponse)
async def marketplace_page(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse("marketplace.html", {"request": request})

# ── Auth API ──────────────────────────────────────────────────────────────────

@app.post("/auth/register")
async def api_register(
    request:      Request,
    username:     str  = Form(...),
    email:        str  = Form(...),
    password:     str   = Form(default=""),
    display_name: str  = Form(default=""),
    is_minor:     bool = Form(default=False),
    db: Session = Depends(get_db)
):
    try:
        ip = get_client_ip(request)
        enforce_rate_limit(ip, "register")
    except Exception:
        pass

    # Sanitize all inputs
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
        result = register_user(db, u["value"], e["value"], "",
                               d["value"], is_minor)
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
    password:     str   = Form(default=""),
    db: Session = Depends(get_db)
):
    try:
        ip = get_client_ip(request)
        enforce_rate_limit(ip, "login")
    except Exception:
        pass

    # Sanitize inputs
    u = sanitizer.sanitize_username(username)
    if not u["ok"]:
        return JSONResponse({"ok": False, "error": u["error"]}, status_code=400)

    result = login_user(db, u["value"], password)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=401)

    # Clear login cooldown on success
    rate_limiter.clear_cooldown(ip, "login")

    return JSONResponse({
        "ok":    True,
        "token": result["token"],
        "user":  {"id": result["user"].id, "username": result["user"].username}
    })

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

    # Sanitize content
    c = sanitizer.sanitize_text(content, max_length=10000)
    if not c["ok"]:
        return JSONResponse({"ok": False, "error": c["error"]}, status_code=400)

    # Validate post type
    allowed_types = {"text", "image", "video", "audio", "live"}
    if post_type not in allowed_types:
        return JSONResponse({"ok": False, "error": "Invalid post type."}, status_code=400)

    result = posts.create(db, current_user, post_type,
                          content=c["value"],
                          is_news=is_news,
                          is_political=is_political)
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
            "id":            post.id,
            "author":        post.author.username if post.author else "unknown",
            "content":       post.content,
            "post_type":     post.post_type.value,
            "community_score": post.community_score,
            "view_count":    post.view_count,
            "published_at":  post.published_at.isoformat() if post.published_at else None,
            "reason":        posts.get_feed_reason(post, current_user),
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

# ── Fingerprint API (Circle only) ─────────────────────────────────────────────

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
    result = fingerprint.human_review(
        db, post_id, current_user.username, decision, reason, notes
    )
    return JSONResponse(result)

# ── Circle API ────────────────────────────────────────────────────────────────

@app.post("/api/circle/appeal/{post_id}")
async def api_appeal(
    post_id: int,
    reason:  str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify the poster is the one appealing
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post or post.author_id != current_user.id:
        raise HTTPException(403, "You can only appeal your own posts.")
    result = circle.open_appeal(db, post_id, reason)
    return JSONResponse(result)

@app.get("/api/codex")
async def api_codex():
    return JSONResponse({
        "ok":       True,
        "platform": TheCommonsCodex.PLATFORM,
        "spirit":   TheCommonsCodex.SPIRIT,
        "sovereign": TheCommonsCodex.SOVEREIGN,
        "laws":     TheCommonsCodex.LAWS,
        "sources":  fingerprint.get_verified_sources(),
    })


# ── Preference API ────────────────────────────────────────────────────────────

@app.get("/api/preferences")
async def api_get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get your full preference profile.
    Transparent — you can see exactly what The Commons knows about your interests.
    """
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
    """Reset your preference profile completely. Fresh start."""
    result = preference_engine.reset_preferences(db, current_user.id)
    return JSONResponse(result)

@app.post("/api/posts/{post_id}/watch")
async def api_record_watch(
    post_id:      int,
    watch_percent: float = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Record how much of a video the user watched."""
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
    """
    Personalized feed — learns from what you value.
    Every post shows why it was chosen. Nothing is hidden.
    """
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


# ── Surplus Donation API ──────────────────────────────────────────────────────

@app.get("/giving")
async def giving_page(request: Request, db: Session = Depends(get_db)):
    """Public page showing every donation ever made. Full transparency."""
    record = surplus_manager.get_public_record(db)
    return templates.TemplateResponse("giving.html", {
        "request": request,
        "donations": record,
        "codex": TheCommonsCodex,
    })

@app.get("/api/giving")
async def api_giving(db: Session = Depends(get_db)):
    """Public API — full donation history."""
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
    """Sovereign Human T.L. Powers designates a humanitarian cause."""
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required. Codex Law 17.")
    from datetime import datetime
    result = surplus_manager.designate_donation(
        db,
        datetime.fromisoformat(period_start),
        datetime.fromisoformat(period_end),
        operating_costs,
        total_collected,
        cause_name,
        cause_url,
        cause_description,
        public_note,
    )
    return JSONResponse(result)

@app.post("/api/giving/confirm/{donation_id}")
async def api_confirm_donation(
    donation_id:  int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm donation was sent."""
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required.")
    result = surplus_manager.confirm_donation(db, donation_id)
    return JSONResponse(result)

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

# ── Marketplace API ───────────────────────────────────────────────────────────

@app.get("/api/marketplace")
async def api_marketplace(
    limit:  int = 40,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    products = commerce.get_marketplace(db, limit, offset)
    result = []
    for p in products:
        seller = db.query(__import__('commons.database', fromlist=['SellerProfile']).SellerProfile).filter_by(id=p.seller_id).first()
        seller_user = db.query(User).filter_by(id=seller.user_id).first() if seller else None
        result.append({
            "id":            p.id,
            "name":          p.name,
            "description":   p.description,
            "price":         p.price,
            "media_path":    p.media_path,
            "community_score": p.community_score,
            "seller":        seller_user.username if seller_user else "unknown",
            "business_type": seller.business_type if seller else "unknown",
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
    name:        str   = Form(...),
    description: str   = Form(default=""),
    price:       float = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = commerce.create_product(db, current_user, name, description, price)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
    return JSONResponse({"ok": True, "product_id": result["product"].id})

@app.post("/api/marketplace/purchase")
async def api_purchase(
    product_ids:  str  = Form(...),  # comma-separated: "1,2,3"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    One order = one $1 fee. No matter how many items.
    Pass product_ids as comma-separated string: "1" or "1,2,3"
    """
    try:
        ids = [int(x.strip()) for x in product_ids.split(",") if x.strip()]
    except ValueError:
        return JSONResponse({"ok": False, "error": "Invalid product IDs."}, status_code=400)

    result = commerce.initiate_purchase(db, current_user, ids)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
    return JSONResponse({
        "ok":        True,
        "breakdown": result["breakdown"],
        "order_id":  result["order"].id,
    })

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
async def api_platform_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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


# --- Magic Link Auth ---

@app.post("/auth/magic/request")
async def request_magic_link(
    request: Request,
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        return JSONResponse({"ok": False, "error": "No account with that email."}, status_code=400)
    token = generate_magic_token(email.lower().strip(), db)
    sent = send_magic_link(email.lower().strip(), token)
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
        response.set_cookie("token", jwt_token, httponly=True, max_age=60*60*24*30)
        return response
    except Exception as e:
        return HTMLResponse(f"<h2>Error: {str(e)}</h2>")
