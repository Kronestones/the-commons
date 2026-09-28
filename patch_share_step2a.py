#!/usr/bin/env python3
"""Share-post step 2a (backend only): PostManager.share() + POST /api/posts/{id}/share."""
import re, sys

POSTS_PY = "commons/posts.py"
MAIN_PY = "main.py"

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

SHARE_METHOD = '''    # ── Share ─────────────────────────────────────────────────────────────────

    def share(self, db: Session, author: User, original_id: int, caption: str = "") -> dict:
        """Share a published post to the author's own profile (and their followers' feeds).
        A share is a normal Post row whose shared_post_id points at the original."""
        from .fingerprint import check_zero_tolerance
        from datetime import datetime as _dt

        caption = (caption or "").strip()
        if len(caption) > 1000:
            return {"ok": False, "error": "Caption exceeds 1,000 character limit."}
        if caption and check_zero_tolerance(caption):
            return {"ok": False, "error": "Your caption contains content that is not permitted on The Commons."}

        target = db.query(Post).filter(Post.id == original_id).first()
        # sharing a share means sharing the original post
        if target is not None and target.shared_post_id:
            target = db.query(Post).filter(Post.id == target.shared_post_id).first()

        if (target is None or target.status != PostStatus.PUBLISHED
                or target.author is None or not target.author.is_active):
            return {"ok": False, "error": "That post isn't available to share."}
        if target.author_id == author.id:
            return {"ok": False, "error": "You can't share your own post."}

        already = (db.query(Post)
                     .filter(Post.author_id == author.id,
                             Post.shared_post_id == target.id,
                             Post.status != PostStatus.REMOVED)
                     .first())
        if already:
            return {"ok": False, "error": "You've already shared this post."}

        post = Post(
            author_id      = author.id,
            post_type      = PostType.TEXT,
            content        = caption,
            media_path     = "",
            is_news        = False,
            is_political   = False,
            shared_post_id = target.id,
            status         = PostStatus.PENDING,
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        if caption:
            # the only new content is the caption, so that is what Fingerprint scans
            fingerprint.scan(db, post)
            db.refresh(post)
        else:
            # a bare share adds no new content; the original was already verified
            post.status = PostStatus.PUBLISHED
            post.published_at = _dt.utcnow()
            db.commit()
            db.refresh(post)

        return {"ok": True, "post": post}

'''

ROUTE = '''@app.post("/api/posts/{post_id}/share")
async def api_share_post(
    request:      Request,
    post_id:      int,
    caption:      str  = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ip = get_client_ip(request)
    enforce_rate_limit(ip, "post")

    c = sanitizer.sanitize_text(caption, max_length=1000)
    if not c["ok"]:
        return JSONResponse({"ok": False, "error": c["error"]}, status_code=400)

    result = posts.share(db, current_user, post_id, c["value"])
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)

    post = result["post"]
    return JSONResponse({
        "ok":      True,
        "post_id": post.id,
        "status":  post.status.value,
        "message": (
            "Shared to your profile." if post.status == PostStatus.PUBLISHED
            else "Your share is being verified and will appear shortly."
        )
    })

'''

posts_src = read(POSTS_PY)
main_src = read(MAIN_PY)
new_posts = new_main = None

if "def share(self" in posts_src:
    print("posts.py already has share(); skipping.")
else:
    hits = list(re.finditer(r"^    # ── Feed .*$", posts_src, flags=re.M))
    if len(hits) == 1:
        i = hits[0].start()
    else:
        hits = list(re.finditer(r"^    def get_feed\(self", posts_src, flags=re.M))
        if len(hits) != 1:
            sys.exit("ABORT: could not find where to insert share() in posts.py")
        i = hits[0].start()
    new_posts = posts_src[:i] + SHARE_METHOD + posts_src[i:]

ANCHOR = '@app.post("/api/posts/{post_id}/vote")'
if "api_share_post" in main_src:
    print("main.py already has the share route; skipping.")
else:
    if main_src.count(ANCHOR) != 1:
        sys.exit("ABORT: vote route anchor found %d times in main.py" % main_src.count(ANCHOR))
    new_main = main_src.replace(ANCHOR, ROUTE + ANCHOR)

if new_posts is not None:
    write(POSTS_PY, new_posts); print("patched", POSTS_PY)
if new_main is not None:
    write(MAIN_PY, new_main); print("patched", MAIN_PY)
