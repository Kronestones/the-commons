"""
patch_add_chat_routes.py

Adds chat API routes to main.py. Uses the same manual cookie-token
read + decode pattern already proven working in home() and other
routes today — NOT get_current_user_optional, which exists in
commons/auth.py but is unused anywhere else and has an unusual
signature that likely wouldn't resolve correctly via FastAPI's normal
dependency injection.

Run once from your project root:
    python3 patch_add_chat_routes.py
"""

PATH = "main.py"

ANCHOR = '''    return JSONResponse({"ok": True, "outlets": outlets_data})'''

NEW = '''    return JSONResponse({"ok": True, "outlets": outlets_data})

# ── Chat ────────────────────────────────────────────────────────────────────

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, db: Session = Depends(get_db)):
    from commons.auth import decode_token
    current_username = None
    token = request.cookies.get("token", "")
    if token:
        payload = decode_token(token)
        if payload:
            current_username = payload.get("username")
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "current_username": current_username,
    })

@app.get("/api/chat/messages")
async def api_chat_messages(request: Request, db: Session = Depends(get_db)):
    from commons.auth import decode_token
    from commons.chat import chat_manager
    viewer = None
    token = request.cookies.get("token", "")
    if token:
        payload = decode_token(token)
        if payload:
            viewer = db.query(User).filter(User.id == int(payload.get("sub", 0))).first()

    messages = chat_manager.get_recent_messages(db, viewer)
    if viewer:
        for m in messages:
            m["is_self"] = (m["author_id"] == viewer.id)
    else:
        for m in messages:
            m["is_self"] = False

    return JSONResponse({"ok": True, "messages": messages})

@app.post("/api/chat/messages")
async def api_chat_send(
    message: str = Form(...),
    reply_to_id: int = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.chat import chat_manager
    result = chat_manager.send_message(db, current_user, message, reply_to_id)
    return JSONResponse(result)

@app.post("/api/chat/report")
async def api_chat_report(
    message_id: int = Form(...),
    reason: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.chat import chat_manager
    result = chat_manager.report_message(db, message_id, current_user, reason)
    return JSONResponse(result)

@app.post("/api/chat/block")
async def api_chat_block(
    blocked_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.chat import chat_manager
    result = chat_manager.block_user(db, current_user, blocked_id)
    return JSONResponse(result)

@app.get("/api/chat/moderation/pending")
async def api_chat_moderation_pending(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.chat import chat_manager
    if current_user.role.value.upper() != "SOVEREIGN":
        return JSONResponse({"ok": False, "error": "Sovereign access only."}, status_code=403)
    pending = chat_manager.get_pending_review(db)
    return JSONResponse({"ok": True, "pending": pending})

@app.post("/api/chat/moderation/confirm-removal")
async def api_chat_moderation_confirm(
    message_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.chat import chat_manager
    if current_user.role.value.upper() != "SOVEREIGN":
        return JSONResponse({"ok": False, "error": "Sovereign access only."}, status_code=403)
    result = chat_manager.confirm_removal(db, message_id)
    return JSONResponse(result)

@app.post("/api/chat/moderation/restore")
async def api_chat_moderation_restore(
    message_id: int = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from commons.chat import chat_manager
    if current_user.role.value.upper() != "SOVEREIGN":
        return JSONResponse({"ok": False, "error": "Sovereign access only."}, status_code=403)
    result = chat_manager.restore_message(db, message_id)
    return JSONResponse(result)'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "/api/chat/messages" in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting.")
        return

    content = content.replace(ANCHOR, NEW, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched main.py successfully.")


if __name__ == "__main__":
    main()
