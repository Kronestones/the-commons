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
from commons.social      import social, Like, Comment, Share
from commons.parental    import parental, ParentalControl
from commons.features    import (
    follow_manager, profile_manager, notification_manager,
    search_manager, bookmark_manager, creator_stats,
    trending_manager, dm_manager,
    Follow, Notification, Hashtag, PostHashtag, Bookmark, DirectMessage
)
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
    # ── Fast startup — Render times out if this takes too long ───────────────
    # Database first — must complete before accepting requests
    init_db()

    # Register all tables
    from commons.preferences import UserTopicPreference, UserCreatorAffinity, UserContentTypePreference, WatchEvent
    from commons.social import Like, Comment, Share
    from commons.parental import ParentalControl
    from commons.features import Follow, Notification, Hashtag, PostHashtag, Bookmark, DirectMessage
    from commons.database import Base, engine
    Base.metadata.create_all(bind=engine)

    # ── Non-critical startup — runs after platform is ready ───────────────────
    import threading

    def background_startup():
        try:
            revival.startup_check()
            heartbeat.start()
        except Exception as e:
            print(f"[STARTUP] Background startup warning: {e}")

    threading.Thread(target=background_startup, daemon=True).start()

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
    password:     str  = Form(...),
    display_name: str  = Form(default=""),
    is_minor:     bool = Form(default=False),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    enforce_rate_limit(ip, "register")

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

    result = register_user(db, u["value"], e["value"], password,
                           d["value"], is_minor)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
    return JSONResponse({
        "ok":    True,
        "token": result["token"],
        "user":  {"id": result["user"].id, "username": result["user"].username}
    })

@app.post("/auth/login")
async def api_login(
    request:  Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    enforce_rate_limit(ip, "login")

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



# ── Social API ────────────────────────────────────────────────────────────────

@app.post("/api/posts/{post_id}/like")
async def api_like(
    post_id:      int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = social.toggle_like(db, current_user, post_id)
    return JSONResponse(result)

@app.get("/api/posts/{post_id}/comments")
async def api_get_comments(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    comments = social.get_comments(db, post_id, current_user)
    return JSONResponse({"ok": True, "comments": comments})

@app.post("/api/posts/{post_id}/comments")
async def api_add_comment(
    post_id:      int,
    content:      str = Form(...),
    parent_id:    int = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = social.add_comment(db, current_user, post_id, content, parent_id)
    return JSONResponse(result)

@app.delete("/api/comments/{comment_id}")
async def api_remove_comment(
    comment_id:   int,
    reason:       str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = social.remove_comment(db, comment_id, current_user, reason)
    return JSONResponse(result)

@app.post("/api/posts/{post_id}/share")
async def api_share(
    post_id:      int,
    note:         str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = social.share_post(db, current_user, post_id, note)
    return JSONResponse(result)


# ── Follow API ────────────────────────────────────────────────────────────────

@app.post("/api/users/{user_id}/follow")
async def api_follow(
    user_id:      int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = follow_manager.toggle_follow(db, current_user, user_id)
    return JSONResponse(result)

@app.get("/api/users/{username}/profile")
async def api_profile(
    username:     str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = profile_manager.get_profile(db, username, current_user)
    if not profile:
        raise HTTPException(404, "User not found")
    return JSONResponse({"ok": True, "profile": profile})

@app.post("/api/profile/bio")
async def api_update_bio(
    bio:          str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_bio(db, current_user, bio))

@app.post("/api/profile/display-name")
async def api_update_display_name(
    display_name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(profile_manager.update_display_name(db, current_user, display_name))

@app.get("/api/feed/following")
async def api_following_feed(
    limit:  int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    posts = follow_manager.get_following_feed(db, current_user, limit, offset)
    return JSONResponse({"ok": True, "feed": [
        {"id": p.id, "content": p.content, "author": p.author.username if p.author else "unknown",
         "post_type": p.post_type.value, "community_score": p.community_score,
         "published_at": p.published_at.isoformat() if p.published_at else None}
        for p in posts
    ], "mode": "following"})

# ── Notifications API ─────────────────────────────────────────────────────────

@app.get("/api/notifications")
async def api_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifs  = notification_manager.get_notifications(db, current_user)
    unread  = notification_manager.unread_count(db, current_user)
    return JSONResponse({"ok": True, "notifications": notifs, "unread_count": unread})

@app.post("/api/notifications/read")
async def api_mark_read(
    notification_id: int = Form(default=None),
    current_user:    User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(notification_manager.mark_read(db, current_user, notification_id))

# ── Search API ────────────────────────────────────────────────────────────────

@app.get("/api/search")
async def api_search(
    q:            str,
    type:         str = "all",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = search_manager.search(db, q, type, current_user)
    return JSONResponse(result)

@app.get("/api/hashtag/{tag}")
async def api_hashtag(
    tag:          str,
    limit:        int = 20,
    offset:       int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    posts = search_manager.get_hashtag_posts(db, tag, limit, offset)
    return JSONResponse({"ok": True, "tag": tag, "posts": posts})

# ── Bookmarks API ─────────────────────────────────────────────────────────────

@app.post("/api/posts/{post_id}/bookmark")
async def api_bookmark(
    post_id:      int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(bookmark_manager.toggle_bookmark(db, current_user, post_id))

@app.get("/api/bookmarks")
async def api_get_bookmarks(
    limit:        int = 20,
    offset:       int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved = bookmark_manager.get_bookmarks(db, current_user, limit, offset)
    return JSONResponse({"ok": True, "bookmarks": saved})

# ── Creator Stats API ─────────────────────────────────────────────────────────

@app.get("/api/stats")
async def api_creator_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse({"ok": True, "stats": creator_stats.get_stats(db, current_user)})

# ── Trending API ──────────────────────────────────────────────────────────────

@app.get("/api/trending")
async def api_trending(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(trending_manager.get_trending(db, current_user))

# ── Direct Messages API ───────────────────────────────────────────────────────

@app.get("/api/messages")
async def api_inbox(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse({"ok": True, "conversations": dm_manager.get_inbox(db, current_user)})

@app.post("/api/messages/{recipient_id}")
async def api_send_message(
    recipient_id: int,
    content:      str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(dm_manager.send(db, current_user, recipient_id, content))

@app.get("/api/messages/{other_user_id}/conversation")
async def api_conversation(
    other_user_id: int,
    current_user:  User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = dm_manager.get_conversation(db, current_user, other_user_id)
    return JSONResponse({"ok": True, "messages": messages})

# ── Parental Controls API ─────────────────────────────────────────────────────

@app.post("/api/parental/setup")
async def api_parental_setup(
    minor_user_id: int = Form(...),
    pin:           str = Form(...),
    parent_email:  str = Form(default=""),
    db: Session = Depends(get_db)
):
    """Parent sets up PIN control for a minor account."""
    result = parental.setup_parental_control(db, minor_user_id, pin, parent_email)
    return JSONResponse(result)

@app.post("/api/parental/approve")
async def api_parental_approve(
    minor_user_id: int = Form(...),
    pin:           str = Form(...),
    db: Session = Depends(get_db)
):
    """Parent approves minor account with PIN."""
    result = parental.approve_account(db, minor_user_id, pin)
    return JSONResponse(result)

@app.post("/api/parental/change-pin")
async def api_change_pin(
    minor_user_id: int = Form(...),
    old_pin:       str = Form(...),
    new_pin:       str = Form(...),
    db: Session = Depends(get_db)
):
    result = parental.change_pin(db, minor_user_id, old_pin, new_pin)
    return JSONResponse(result)

@app.get("/api/parental/status/{minor_user_id}")
async def api_parental_status(
    minor_user_id: int,
    db: Session = Depends(get_db)
):
    result = parental.get_status(db, minor_user_id)
    return JSONResponse(result)

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
