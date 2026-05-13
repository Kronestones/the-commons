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
from fastapi import FastAPI, Request, Depends, Form, HTTPException, File, UploadFile
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
from commons.maintenance    import maintenance
from commons.circle_assistants import circle_assistants, AssistantAnalysis
from commons.payments        import payment_manager, UserCurrencyPreference, LiveGift, CreatorWallet
from commons.support         import support_manager, SupportTicket, SupportMessage
from commons.blessing        import blessing_manager, BlessingApplication, BlessingVote, MonthlyBlessingRecord
from commons.livestream      import livestream_manager, LiveStream, LiveChatMessage, StreamViewer, StreamGiftEvent, COMING_SOON
from commons.transparency    import transparency_manager, OperatingCostEntry, MonthlyReport
from commons.magic_routes    import router as magic_router
from commons.email_auth      import generate_magic_token, verify_magic_token, send_magic_link, MagicToken
from commons.uploads         import upload_manager
from commons.translation import translation_manager
from commons.captions    import caption_manager, Caption
from commons.features    import (
    follow_manager, profile_manager, notification_manager,
    search_manager, bookmark_manager, creator_stats,
    trending_manager, dm_manager,
    block_manager, report_manager, video_response_manager,
    Follow, Notification, Hashtag, PostHashtag, Bookmark, DirectMessage,
    UserBlock, ContentReport, VideoResponse
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

app.include_router(magic_router)

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
    from commons.features import Follow, Notification, Hashtag, PostHashtag, Bookmark, DirectMessage, UserBlock, ContentReport, VideoResponse
    from commons.captions import Caption
    from commons.circle_assistants import AssistantAnalysis
    from commons.payments import UserCurrencyPreference, LiveGift, CreatorWallet
    from commons.support import SupportTicket, SupportMessage
    from commons.blessing import BlessingApplication, BlessingVote, MonthlyBlessingRecord
    from commons.livestream import LiveStream, LiveChatMessage, StreamViewer, StreamGiftEvent
    from commons.transparency import OperatingCostEntry, MonthlyReport
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
    # Decode token from Authorization header or cookie for template use
    current_username = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        from commons.auth import decode_token
        payload = decode_token(auth_header[7:])
        if payload:
            current_username = payload.get("username")
    return templates.TemplateResponse("index.html", {
        "request":          request,
        "posts":            recent_posts,
        "version":          VERSION,
        "current_username": current_username,
    })

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/profile/edit", response_class=HTMLResponse)
async def profile_edit_page(request: Request):
    return templates.TemplateResponse("profile_edit.html", {"request": request})

@app.get("/profile/{username}", response_class=HTMLResponse)
async def profile_page(username: str, request: Request):
    return templates.TemplateResponse("profile.html", {
        "request":  request,
        "username": username,
    })

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

@app.get("/api/test-auth")
async def test_auth(current_user: User = Depends(get_current_user)):
    return JSONResponse({"ok": True, "user": current_user.username, "role": current_user.role.value})

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
        from commons.database import CommunityVote
        user_voted = db.query(CommunityVote).filter(
            CommunityVote.post_id == post.id,
            CommunityVote.user_id == current_user.id
        ).first() is not None
        feed.append({
            "id":            post.id,
            "author":        post.author.username if post.author else "unknown",
            "content":       post.content,
            "post_type":     post.post_type.value,
            "community_score": post.community_score,
            "view_count":    post.view_count,
            "published_at":  post.published_at.isoformat() if post.published_at else None,
            "reason":        posts.get_feed_reason(post, current_user),
            "user_voted":    user_voted,
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






# ── Support API ───────────────────────────────────────────────────────────────

@app.post("/api/support/chat")
async def api_support_chat(
    message:      str = Form(...),
    ticket_id:    int = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """AI-powered support chat. Escalates to Circle if needed."""
    result = support_manager.get_ai_response(message)

    # Save the conversation
    support_manager.save_message(db, ticket_id, current_user.id, "user", message)
    support_manager.save_message(db, ticket_id, current_user.id, "ai", result["response"])

    # Create ticket if escalation needed
    if result["escalate"]:
        ticket = support_manager.create_ticket(
            db, current_user.id,
            subject     = message[:200],
            description = message,
            category    = result["category"]
        )
        return JSONResponse({
            "ok":       True,
            "response": result["response"],
            "escalated": True,
            "ticket_id": ticket["ticket_id"],
        })

    return JSONResponse({
        "ok":       True,
        "response": result["response"],
        "escalated": False,
    })

@app.get("/api/support/faq")
async def api_faq():
    """Get FAQ — common questions answered."""
    return JSONResponse({"ok": True, "faq": support_manager.get_faq()})

@app.post("/api/support/ticket")
async def api_create_ticket(
    subject:      str = Form(...),
    description:  str = Form(...),
    category:     str = Form(default="general"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = support_manager.create_ticket(db, current_user.id, subject, description, category)
    return JSONResponse(result)

@app.get("/api/support/tickets")
async def api_get_tickets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required.")
    tickets = support_manager.get_open_tickets(db)
    return JSONResponse({"ok": True, "tickets": tickets})

@app.post("/api/support/tickets/{ticket_id}/resolve")
async def api_resolve_ticket(
    ticket_id:    int,
    resolution:   str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required.")
    return JSONResponse(support_manager.resolve_ticket(db, ticket_id, resolution))

# ── Transparency API ──────────────────────────────────────────────────────────

@app.get("/transparency")
async def transparency_page(request: Request, db: Session = Depends(get_db)):
    reports = transparency_manager.get_public_reports(db)
    return templates.TemplateResponse("transparency.html", {
        "request": request,
        "reports": reports,
    })

@app.get("/api/transparency")
async def api_transparency(db: Session = Depends(get_db)):
    return JSONResponse({
        "ok":      True,
        "reports": transparency_manager.get_public_reports(db),
        "note":    "Full operating cost transparency. Codex Law 5."
    })

@app.post("/api/transparency/cost")
async def api_add_cost(
    month:        str   = Form(...),
    category:     str   = Form(...),
    description:  str   = Form(...),
    amount_usd:   float = Form(...),
    is_recurring: bool  = Form(default=False),
    current_user: User  = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required.")
    return JSONResponse(transparency_manager.add_cost(
        db, month, category, description, amount_usd, is_recurring
    ))

@app.post("/api/transparency/publish/{month}")
async def api_publish_report(
    month:         str,
    total_fees:    float = Form(...),
    notes:         str   = Form(default=""),
    current_user:  User  = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required.")
    return JSONResponse(transparency_manager.publish_monthly_report(
        db, month, total_fees, notes
    ))



@app.get("/live")
async def live_page(request: Request):
    """Live streaming coming soon page."""
    return templates.TemplateResponse("live.html", {"request": request})

# ── Live Streaming API ────────────────────────────────────────────────────────

@app.get("/api/live/status")
async def api_live_status():
    """Coming soon status for live streaming."""
    return JSONResponse({"ok": True, "live_streaming": COMING_SOON})

@app.get("/api/live/streams")
async def api_active_streams(db: Session = Depends(get_db)):
    """Get all currently live streams."""
    streams = livestream_manager.get_active_streams(db)
    return JSONResponse({"ok": True, "streams": streams, "count": len(streams)})

@app.post("/api/live/create")
async def api_create_stream(
    title:         str  = Form(...),
    description:   str  = Form(default=""),
    category:      str  = Form(default="general"),
    chat_enabled:  bool = Form(default=True),
    gifts_enabled: bool = Form(default=True),
    current_user:  User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(livestream_manager.create_stream(
        db, current_user, title, description,
        category, None, chat_enabled, gifts_enabled
    ))

@app.post("/api/live/{stream_id}/go-live")
async def api_go_live(
    stream_id:    int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(livestream_manager.go_live(db, stream_id, current_user))

@app.post("/api/live/{stream_id}/end")
async def api_end_stream(
    stream_id:    int,
    make_replay:  bool = Form(default=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(livestream_manager.end_stream(db, stream_id, current_user, make_replay))

@app.get("/api/live/{stream_id}")
async def api_stream_info(
    stream_id: int,
    db: Session = Depends(get_db)
):
    info = livestream_manager.get_stream_info(db, stream_id)
    if not info:
        raise HTTPException(404, "Stream not found.")
    return JSONResponse({"ok": True, "stream": info})

@app.post("/api/live/{stream_id}/join")
async def api_join_stream(
    stream_id:    int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(livestream_manager.join_stream(db, stream_id, current_user.id))

@app.post("/api/live/{stream_id}/leave")
async def api_leave_stream(
    stream_id:    int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(livestream_manager.leave_stream(db, stream_id, current_user.id))

@app.post("/api/live/{stream_id}/chat")
async def api_live_chat(
    stream_id:    int,
    message:      str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(livestream_manager.send_chat(db, stream_id, current_user, message))

@app.get("/api/live/{stream_id}/chat")
async def api_get_chat(
    stream_id: int,
    limit:     int = 50,
    since_id:  int = 0,
    db: Session = Depends(get_db)
):
    messages = livestream_manager.get_chat(db, stream_id, limit, since_id)
    return JSONResponse({"ok": True, "messages": messages})

@app.delete("/api/live/chat/{message_id}")
async def api_remove_chat(
    message_id:   int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(livestream_manager.remove_chat_message(db, message_id, current_user))

@app.post("/api/live/chat/{message_id}/pin")
async def api_pin_chat(
    message_id:   int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(livestream_manager.pin_chat_message(db, message_id, current_user))

# ── Monthly Blessing API ──────────────────────────────────────────────────────

@app.get("/blessing")
async def blessing_page(request: Request, db: Session = Depends(get_db)):
    """Public Blessing page — current month voting and full history."""
    from datetime import datetime
    month   = datetime.utcnow().strftime("%Y-%m")
    current = blessing_manager.get_current_applications(db, month)
    history = blessing_manager.get_public_record(db)
    return templates.TemplateResponse("blessing.html", {
        "request": request,
        "month":   month,
        "current": current,
        "history": history,
    })

@app.get("/api/blessing/current")
async def api_blessing_current(db: Session = Depends(get_db)):
    from datetime import datetime
    month = datetime.utcnow().strftime("%Y-%m")
    return JSONResponse({
        "ok":           True,
        "month":        month,
        "applications": blessing_manager.get_current_applications(db, month),
        "note":         "Codex Law 18 — The Monthly Blessing. One person. One month. Community chosen."
    })

@app.get("/api/blessing/history")
async def api_blessing_history(db: Session = Depends(get_db)):
    return JSONResponse({
        "ok":      True,
        "history": blessing_manager.get_public_record(db)
    })

@app.post("/api/blessing/apply")
async def api_blessing_apply(
    need_category:    str   = Form(...),
    need_description: str   = Form(...),
    amount_needed:    float = Form(...),
    is_family:        bool  = Form(default=False),
    family_size:      int   = Form(default=1),
    current_user:     User  = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime
    month = datetime.utcnow().strftime("%Y-%m")
    result = blessing_manager.apply(
        db, current_user, month,
        need_category, need_description,
        amount_needed, is_family, family_size
    )

    # If application successful, run all five Circle assistants
    if result.get("ok"):
        from commons.circle_assistants import circle_assistants, CIRCLE_ASSISTANT_MAP
        context = {
            "is_family":       is_family,
            "family_size":     family_size,
            "amount_needed":   amount_needed,
            "need_category":   need_category,
            "human_reviewed":  False,
        }
        content = f"Blessing Application\nCategory: {need_category}\nNeed: {need_description}\nAmount: ${amount_needed}"
        
        # Run all five assistants
        for member_name in CIRCLE_ASSISTANT_MAP.keys():
            try:
                circle_assistants.analyze_for_member(
                    db,
                    circle_member = member_name,
                    post_id       = None,
                    content       = content,
                    context       = context
                )
            except Exception as e:
                print(f"[ASSISTANTS] {member_name} analysis error: {e}")
        
        result["assistant_note"] = (
            "Your application has been received. "
            "Ember, Vela, Sophia, Echo, and Threshold are reviewing it now. "
            "The community will vote once the review is complete."
        )

    return JSONResponse(result)

@app.post("/api/blessing/vote/{application_id}")
async def api_blessing_vote(
    application_id: int,
    current_user:   User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import datetime
    month = datetime.utcnow().strftime("%Y-%m")
    return JSONResponse(blessing_manager.vote(db, current_user, application_id, month))

@app.post("/api/blessing/verify/{application_id}")
async def api_blessing_verify(
    application_id: int,
    decision:       str = Form(...),
    circle_notes:   str = Form(default=""),
    current_user:   User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required.")
    return JSONResponse(blessing_manager.verify_application(
        db, application_id, decision, circle_notes, current_user.username
    ))

@app.post("/api/blessing/close/{month}")
async def api_blessing_close(
    month:             str,
    surplus_amount:    float = Form(...),
    sovereign_message: str   = Form(default=""),
    current_user:      User  = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required.")
    return JSONResponse(blessing_manager.close_month(db, month, surplus_amount, sovereign_message))

# ── Checkout API ─────────────────────────────────────────────────────────────

@app.get("/api/checkout/breakdown")
async def api_checkout_breakdown(
    product_price: float = 0.0,
    gift_value:    float = 0.0,
    include_platform_fee: bool = True,
):
    """
    Get a full transparent price breakdown before checkout.
    Shows exactly where every dollar goes.
    No surprises. Codex Law 5.
    """
    from commons.payments import build_checkout_breakdown
    breakdown = build_checkout_breakdown(
        product_price        = product_price,
        platform_fee         = 1.00 if include_platform_fee else 0.0,
        gift_value           = gift_value,
    )
    return JSONResponse({"ok": True, **breakdown})

# ── Currency API ──────────────────────────────────────────────────────────────

@app.get("/api/currencies")
async def api_currencies():
    return JSONResponse({"ok": True, "currencies": payment_manager.get_supported_currencies()})

@app.post("/api/currency/preference")
async def api_set_currency(
    currency:     str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(payment_manager.set_currency_preference(db, current_user.id, currency))

# ── Live Gifts API ────────────────────────────────────────────────────────────

@app.get("/api/gifts/types")
async def api_gift_types():
    return JSONResponse({"ok": True, "gifts": payment_manager.get_gift_types()})

@app.post("/api/gifts/send")
async def api_send_gift(
    live_post_id: int = Form(...),
    creator_id:   int = Form(...),
    gift_type:    str = Form(...),
    currency:     str = Form(default="USD"),
    message:      str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    result = payment_manager.send_gift(
        db, current_user.id, creator_id,
        live_post_id, gift_type, currency, message
    )
    return JSONResponse(result)

@app.get("/api/gifts/live/{live_post_id}")
async def api_live_gifts(
    live_post_id: int,
    db: Session = Depends(get_db)
):
    gifts = payment_manager.get_live_gifts(db, live_post_id)
    return JSONResponse({"ok": True, "gifts": gifts})

@app.get("/api/wallet")
async def api_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(payment_manager.get_creator_wallet(db, current_user.id))

# ── Upload API ────────────────────────────────────────────────────────────────

@app.get("/api/upload/limits")
async def api_upload_limits():
    return JSONResponse({"ok": True, "limits": upload_manager.get_upload_limits()})

@app.get("/api/upload/ai-tools")
async def api_ai_tools():
    return JSONResponse({"ok": True, "tools": upload_manager.get_ai_tools()})

@app.post("/api/upload")
async def api_upload(
    request:        Request,
    post_type:      str  = Form(...),
    content:        str  = Form(default=""),
    is_ai_generated: bool = Form(default=False),
    ai_tool:        str  = Form(default=""),
    is_news:        bool = Form(default=False),
    is_political:   bool = Form(default=False),
    current_user:   User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload media and create a post.
    Supports all major video, image, and audio formats.
    AI-generated content welcome — disclosure optional but encouraged.
    """
    from fastapi import UploadFile, File
    import json

    # Get file from form
    form    = await request.form()
    file    = form.get("file")

    media_path = ""
    if file and hasattr(file, "filename") and file.filename:
        file_data = await file.read()
        save_result = await upload_manager.save_upload(
            file_data, file.filename, current_user.id
        )
        if not save_result["ok"]:
            return JSONResponse({"ok": False, "error": save_result["error"]}, status_code=400)
        media_path = save_result["path"]
        post_type  = save_result["media_type"]

    # Build AI disclosure
    ai_disclosure = upload_manager.build_ai_disclosure(ai_tool, is_ai_generated)

    # Sanitize content
    c = sanitizer.sanitize_text(content, max_length=10000)
    if not c["ok"]:
        return JSONResponse({"ok": False, "error": c["error"]}, status_code=400)

    # Add AI disclosure to content if applicable
    final_content = c["value"]
    if ai_disclosure.get("is_ai_generated") and ai_disclosure.get("disclosure_text"):
        final_content = final_content  # Store disclosure separately in future

    from commons.posts import posts
    result = posts.create(
        db, current_user, post_type,
        content      = final_content,
        media_path   = media_path,
        is_news      = is_news,
        is_political = is_political,
    )

    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)

    post = result["post"]

    # Index hashtags
    search_manager.index_post_hashtags(db, post)

    # Notify followers
    import threading
    def notify_followers():
        try:
            from commons.database import SessionLocal
            from commons.features import Follow, notification_manager
            db2 = SessionLocal()
            try:
                followers = db2.query(Follow).filter(Follow.following_id == current_user.id).all()
                for f in followers:
                    notification_manager.create(
                        db2, f.follower_id, current_user.id,
                        "post", f"@{current_user.username} posted something new",
                        post_id=post.id
                    )
            finally:
                db2.close()
        except Exception:
            pass
    threading.Thread(target=notify_followers, daemon=True).start()

    return JSONResponse({
        "ok":             True,
        "post_id":        post.id,
        "status":         post.status.value,
        "ai_disclosure":  ai_disclosure,
        "message": (
            "Your post is live." if post.status == PostStatus.PUBLISHED
            else "Your post is being verified and will appear shortly."
        )
    })

# ── Circle Assistant API ──────────────────────────────────────────────────────

@app.post("/api/circle/assistants/analyze/{post_id}")
async def api_assistant_analyze(
    post_id:       int,
    circle_member: str = Form(...),
    current_user:  User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run all four assistants for a Circle member on a post."""
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required.")
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(404, "Post not found.")
    result = circle_assistants.analyze_for_member(
        db, circle_member, post_id, post.content or "",
        context={
            "is_political":   post.is_political,
            "is_news":        post.is_news,
            "human_reviewed": post.status == PostStatus.PUBLISHED,
        }
    )
    return JSONResponse(result)

@app.get("/api/circle/assistants/pending/{circle_member}")
async def api_assistant_pending(
    circle_member: str,
    current_user:  User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending assistant analyses for a Circle member."""
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required.")
    analyses = circle_assistants.get_pending_analyses(db, circle_member)
    return JSONResponse({"ok": True, "analyses": analyses})

@app.post("/api/circle/assistants/reviewed/{analysis_id}")
async def api_assistant_reviewed(
    analysis_id:  int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an assistant analysis as reviewed."""
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required.")
    return JSONResponse(circle_assistants.mark_reviewed(db, analysis_id))

@app.get("/api/circle/assistants/profiles/{circle_member}")
async def api_assistant_profiles(
    circle_member: str,
    current_user:  User = Depends(get_current_user),
):
    """Get the four assistant profiles for a Circle member."""
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required.")
    return JSONResponse(circle_assistants.get_assistant_profiles(circle_member))

# ── Translation API ───────────────────────────────────────────────────────────

@app.post("/api/translate")
async def api_translate(
    text:            str = Form(...),
    target_language: str = Form(...),
    source_language: str = Form(default="auto"),
    current_user: User = Depends(get_current_user),
):
    result = await translation_manager.translate(text, target_language, source_language)
    return JSONResponse(result)

@app.get("/api/translate/languages")
async def api_languages():
    return JSONResponse({
        "ok": True,
        "languages": translation_manager.get_supported_languages()
    })

# ── Captions API ──────────────────────────────────────────────────────────────

@app.get("/api/posts/{post_id}/captions")
async def api_get_captions(
    post_id: int,
    db: Session = Depends(get_db)
):
    return JSONResponse(caption_manager.get_captions(db, post_id))

# ── Maintenance API (Sovereign only) ──────────────────────────────────────────

@app.get("/api/maintenance/status")
async def api_maintenance_status(
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required.")
    return JSONResponse({"ok": True, "status": maintenance.get_status()})

@app.post("/api/maintenance/run")
async def api_maintenance_run(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign authority required.")
    results = maintenance.run()
    return JSONResponse({"ok": True, "results": results})

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
):
    profile = profile_manager.get_profile(db, username, current_user)
    if not profile:
        raise HTTPException(404, "User not found")
    return JSONResponse({"ok": True, "profile": profile})


@app.post("/api/profile/avatar")
async def api_upload_avatar(
    media:        UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    import uuid, aiofiles
    from pathlib import Path
    ext = Path(media.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return JSONResponse({"ok": False, "error": "Image files only."}, status_code=400)
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    path = config.media_dir / filename
    async with aiofiles.open(path, "wb") as f:
        await f.write(await media.read())
    current_user.avatar_path = filename
    db.commit()
    return JSONResponse({"ok": True, "avatar_path": filename})


@app.post("/api/profile/banner")
async def api_upload_banner(
    media:        UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    import uuid, aiofiles
    from pathlib import Path
    ext = Path(media.filename).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        return JSONResponse({"ok": False, "error": "Image files only."}, status_code=400)
    filename = f"banner_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    path = config.media_dir / filename
    async with aiofiles.open(path, "wb") as f:
        await f.write(await media.read())
    current_user.banner_path = filename
    db.commit()
    return JSONResponse({"ok": True, "banner_path": filename})


@app.delete("/api/users/{user_id}")
async def api_delete_user(
    user_id:      int,
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    if user_id == 1:
        return JSONResponse({"ok": False, "error": "This account is protected."}, status_code=403)
    return JSONResponse({"ok": False, "error": "Account deletion not available."}, status_code=403)

@app.post("/api/profile/username")
async def api_change_username(
    username:     str  = Form(...),
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    import re
    username = username.strip()
    
    # Validate format
    if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', username):
        return JSONResponse({"ok": False, "error": "Username must be 3-50 characters. Letters, numbers, underscores and hyphens only."}, status_code=400)
    
    # Check if taken (case-insensitive)
    existing = db.query(User).filter(
        User.username.ilike(username),
        User.id != current_user.id
    ).first()
    if existing:
        return JSONResponse({"ok": False, "error": "That username is already taken."}, status_code=400)
    
    current_user.username = username
    db.commit()
    return JSONResponse({"ok": True, "username": username, "message": "Username updated."})

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
    current_user:  User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Parent sets up PIN control for a minor account."""
    # Only the sovereign or the minor's own account holder may set this up
    if current_user.role.value != "sovereign" and current_user.id != minor_user_id:
        raise HTTPException(403, "You can only set up parental controls on your own account.")
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

# ── Kinto ─────────────────────────────────────────────────────────────────────

@app.get("/kinto", response_class=HTMLResponse)
async def kinto_page():
    """Kinto download page — standalone, separate from The Commons."""
    kinto_html = os.path.join(os.path.dirname(__file__), "static", "kinto.html")
    with open(kinto_html, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# ── Surplus Donation API ──────────────────────────────────────────────────────

@app.get("/giving")
async def giving_page(request: Request, db: Session = Depends(get_db)):
    """Combined Giving, Blessing and Transparency page."""
    from datetime import datetime
    month   = datetime.utcnow().strftime("%Y-%m")
    record  = surplus_manager.get_public_record(db)
    current = blessing_manager.get_current_applications(db, month)
    history = blessing_manager.get_public_record(db)
    reports = transparency_manager.get_public_reports(db)
    return templates.TemplateResponse("giving.html", {
        "request":   request,
        "donations": record,
        "month":     month,
        "current":   current,
        "history":   history,
        "reports":   reports,
        "codex":     TheCommonsCodex,
    })

@app.get("/blessing")
async def blessing_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/giving")

@app.get("/transparency")
async def transparency_redirect():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/giving")

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


# ── Block API ─────────────────────────────────────────────────────────────────

@app.post("/api/users/{user_id}/block")
async def api_block(
    user_id:      int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(block_manager.toggle_block(db, current_user, user_id))

@app.get("/api/blocked")
async def api_get_blocked(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse({"ok": True, "blocked": block_manager.get_blocked_users(db, current_user.id)})

# ── Report API ────────────────────────────────────────────────────────────────

@app.get("/api/report/reasons")
async def api_report_reasons():
    return JSONResponse({"ok": True, "reasons": report_manager.REPORT_REASONS})

@app.post("/api/posts/{post_id}/report")
async def api_report_post(
    post_id:      int,
    reason:       str = Form(...),
    details:      str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(report_manager.submit_report(db, current_user.id, post_id, reason, details))

@app.get("/api/reports/pending")
async def api_pending_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle access required.")
    return JSONResponse({"ok": True, "reports": report_manager.get_pending_reports(db)})

# ── Verified Checkmark ────────────────────────────────────────────────────────

VERIFIED_THRESHOLD = 10000

@app.post("/api/users/{user_id}/check-verified")
async def api_check_verified(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Auto-verify users who reach 10k followers."""
    from commons.features import Follow
    followers = db.query(Follow).filter(Follow.following_id == user_id).count()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found.")
    if followers >= VERIFIED_THRESHOLD and not user.is_verified:
        user.is_verified = True
        db.commit()
        return JSONResponse({"ok": True, "verified": True, "message": "✓ Verified — 10,000 followers reached!"})
    return JSONResponse({"ok": True, "verified": user.is_verified, "followers": followers, "threshold": VERIFIED_THRESHOLD})

# ── Stitch & Duet API ─────────────────────────────────────────────────────────

@app.post("/api/posts/{post_id}/stitch")
async def api_stitch(
    post_id:          int,
    response_post_id: int = Form(...),
    current_user:     User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stitch — respond to someone's video with your own."""
    return JSONResponse(video_response_manager.create_stitch(db, current_user, post_id, response_post_id))

@app.post("/api/posts/{post_id}/duet")
async def api_duet(
    post_id:          int,
    response_post_id: int = Form(...),
    current_user:     User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Duet — side by side video response."""
    return JSONResponse(video_response_manager.create_duet(db, current_user, post_id, response_post_id))

@app.get("/api/posts/{post_id}/responses")
async def api_video_responses(
    post_id: int,
    db: Session = Depends(get_db)
):
    return JSONResponse({"ok": True, "responses": video_response_manager.get_responses(db, post_id)})

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "platform": "The Commons", "spirit": "Power to the People"}

# ── Marketplace API ───────────────────────────────────────────────────────────

@app.get("/api/marketplace")
async def api_marketplace(
    limit:  int = 40,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    from commons.database import SellerProfile
    products = commerce.get_marketplace(db, limit, offset)
    result = []
    for p in products:
        seller = db.query(SellerProfile).filter_by(id=p.seller_id).first()
        seller_user = db.query(User).filter_by(id=seller.user_id).first() if seller else None
        result.append({
            "id":            p.id,
            "name":          p.name,
            "description":   p.description,
            "price":         p.price,
            "media_path":    p.media_path,
            "community_score": p.community_score,
            "seller":        seller_user.username if seller_user else "unknown",
            "seller_user_id": seller_user.id if seller_user else None,
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

@app.delete("/api/posts/{post_id}")
async def api_delete_post(
    post_id:      int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return JSONResponse({"ok": False, "error": "Post not found."}, status_code=404)
    if post.author_id != current_user.id and current_user.role.value not in ("circle", "sovereign"):
        return JSONResponse({"ok": False, "error": "Not your post."}, status_code=403)
    db.delete(post)
    db.commit()
    return JSONResponse({"ok": True})


@app.delete("/api/marketplace/products/{product_id}")
async def api_delete_product(
    product_id:   int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.database import SellerProfile
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return JSONResponse({"ok": False, "error": "Listing not found."}, status_code=404)
    seller = db.query(SellerProfile).filter(
        SellerProfile.id == product.seller_id,
        SellerProfile.user_id == current_user.id
    ).first()
    if not seller and current_user.role.value not in ("circle", "sovereign"):
        return JSONResponse({"ok": False, "error": "Not your listing."}, status_code=403)
    product.is_active = False
    db.commit()
    return JSONResponse({"ok": True})


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

# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host    = config.host,
        port    = config.port,
        reload  = config.debug,
        workers = 1 if config.debug else 4,
    )
