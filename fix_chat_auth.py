#!/usr/bin/env python3
"""
fix_chat_auth.py

Fixes two bugs preventing the chat room from working for logged-in users:

1. /chat rendered its logged-in/logged-out state using server-side Jinja
   (`current_user`), but this app never sets a "token" cookie — the JWT
   lives in localStorage and is only ever checked client-side (same as
   every other page: profile, index, etc). So `current_user` was never
   populated and the page always showed the logged-out prompt.

2. chat.js's sendMessage/reportMessage/blockUser never attached the
   `Authorization: Bearer <token>` header, so even after fixing (1),
   those calls would 401 against routes that require get_current_user.

This patch:
  - Simplifies main.py's chat_page() to stop doing manual cookie/token
    decoding (it was never going to work) and just render the template.
  - Updates templates/chat.html to always render both the composer and
    the login-prompt markup (hidden via inline style), letting chat.js
    decide which to show — matching the site's existing client-side
    auth pattern instead of inventing a new one.
  - Updates static/js/chat.js to determine login state via the site's
    existing global getUsername()/getToken() helpers (from main.js),
    and attaches the Authorization header on all three POST calls.

Safe to run twice: each patch checks whether it's already applied and
skips with a message rather than erroring or double-patching.
"""

import sys
from pathlib import Path

PATCHES = [
    # ---- main.py -----------------------------------------------------
    {
        "file": "main.py",
        "label": "main.py: simplify chat_page() (drop dead cookie-decoding logic)",
        "old_only_fragment": "from commons.auth import decode_token",
        "anchor": '''@app.get("/chat", response_class=HTMLResponse)
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
    })''',
        "new": '''@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    # Login state for /chat is determined entirely client-side (chat.js
    # reads the JWT from localStorage via the site's existing
    # getUsername()/getToken() helpers) since this app never sets a
    # server-side "token" cookie — the old code here decoded a cookie
    # that was never actually being set.
    return templates.TemplateResponse("chat.html", {
        "request": request,
    })''',
    },
    # ---- templates/chat.html: input row -------------------------------
    {
        "file": "templates/chat.html",
        "label": "chat.html: render both composer and login-prompt, let JS toggle",
        "old_only_fragment": "{% if current_user %}",
        "anchor": '''  <div class="chat-input-row">
    {% if current_user %}
      <p class="chat-input-reminder">Be kind. Keep it appropriate for all ages. Never share personal info.</p>
      <form id="chatForm" class="chat-form" autocomplete="off">
        <input
          type="text"
          id="chatInput"
          class="chat-input"
          placeholder="Say something to the Commons…"
          maxlength="500"
          required
        />
        <button type="submit" class="chat-send-btn">Send</button>
      </form>
    {% else %}
      <div class="chat-login-prompt">
        <a href="/login">Log in</a> to join the conversation. You can read along without an account.
      </div>
    {% endif %}
  </div>''',
        "new": '''  <div class="chat-input-row">
    <div class="chat-input-row-loggedin" id="chatInputLoggedIn" style="display:none">
      <p class="chat-input-reminder">Be kind. Keep it appropriate for all ages. Never share personal info.</p>
      <form id="chatForm" class="chat-form" autocomplete="off">
        <input
          type="text"
          id="chatInput"
          class="chat-input"
          placeholder="Say something to the Commons…"
          maxlength="500"
          required
        />
        <button type="submit" class="chat-send-btn">Send</button>
      </form>
    </div>
    <div class="chat-login-prompt" id="chatLoginPrompt" style="display:none">
      <a href="/login">Log in</a> to join the conversation. You can read along without an account.
    </div>
  </div>''',
    },
    # ---- templates/chat.html: drop the dead Jinja script tag ----------
    {
        "file": "templates/chat.html",
        "label": "chat.html: remove dead CURRENT_USERNAME Jinja script (chat.js computes it now)",
        "old_only_fragment": '''window.CURRENT_USERNAME = {{ (current_user.username | tojson) if current_user else "null" }};''',
        "anchor": '''<script>
  window.CURRENT_USERNAME = {{ (current_user.username | tojson) if current_user else "null" }};
</script>
<script src="/static/js/chat.js"></script>''',
        "new": '''<script src="/static/js/chat.js"></script>''',
    },
    # ---- static/js/chat.js: login-state + element refs ---------------
    {
        "file": "static/js/chat.js",
        "label": "chat.js: compute login state client-side, toggle composer vs. login prompt",
        "anchor": '''  let knownMessageIds = new Set();
  let pollTimer = null;''',
        "new": '''  let knownMessageIds = new Set();
  let pollTimer = null;

  // --- Login state (client-side, same pattern as the rest of the site) --
  // main.js (loaded before this file on every page) exposes getUsername()
  // and getToken(), which read the JWT from localStorage. There is no
  // server-side "current_user" for this page — see main.py's chat_page().
  const CURRENT_USERNAME = (typeof getUsername === 'function') ? getUsername() : null;
  const AUTH_TOKEN = (typeof getToken === 'function') ? getToken() : null;
  const chatInputLoggedIn = document.getElementById('chatInputLoggedIn');
  const chatLoginPrompt = document.getElementById('chatLoginPrompt');
  if (CURRENT_USERNAME) {
    if (chatInputLoggedIn) chatInputLoggedIn.style.display = '';
  } else {
    if (chatLoginPrompt) chatLoginPrompt.style.display = '';
  }''',
    },
    {
        "file": "static/js/chat.js",
        "label": "chat.js: use client-computed CURRENT_USERNAME instead of window.CURRENT_USERNAME",
        "old_only_fragment": "if (msg.is_self || !window.CURRENT_USERNAME) {",
        "anchor": "    if (msg.is_self || !window.CURRENT_USERNAME) {",
        "new": "    if (msg.is_self || !CURRENT_USERNAME) {",
    },
    {
        "file": "static/js/chat.js",
        "label": "chat.js: attach Authorization header to sendMessage",
        "anchor": '''    const res = await fetch('/api/chat/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });''',
        "new": '''    const res = await fetch('/api/chat/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + (AUTH_TOKEN || ''),
      },
      body: formData.toString(),
    });''',
    },
    {
        "file": "static/js/chat.js",
        "label": "chat.js: attach Authorization header to reportMessage",
        "anchor": '''      const res = await fetch('/api/chat/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });''',
        "new": '''      const res = await fetch('/api/chat/report', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Bearer ' + (AUTH_TOKEN || ''),
        },
        body: formData.toString(),
      });''',
    },
    {
        "file": "static/js/chat.js",
        "label": "chat.js: attach Authorization header to blockUser",
        "anchor": '''      const res = await fetch('/api/chat/block', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });''',
        "new": '''      const res = await fetch('/api/chat/block', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Authorization': 'Bearer ' + (AUTH_TOKEN || ''),
        },
        body: formData.toString(),
      });''',
    },
]


def apply_patch(patch):
    path = Path(patch["file"])
    if not path.exists():
        print(f"  ABORT: {path} not found.")
        return False

    text = path.read_text()

    # Prefer an explicit "old_only_fragment" (a piece of the ORIGINAL code
    # guaranteed to disappear once patched) for idempotency detection: it's
    # more reliable than checking "is `new` already in the file", since a
    # short/generic replacement string can coincidentally already exist in
    # the unpatched file (false positive) or be a literal prefix of a longer
    # anchor (false negative on a second run). Fall back to "new in text"
    # only for patches where the two never overlap.
    if "old_only_fragment" in patch:
        already_applied = patch["old_only_fragment"] not in text
    else:
        already_applied = patch["new"] in text

    if already_applied:
        print(f"  Already applied — skipping: {patch['label']}")
        return True

    count = text.count(patch["anchor"])
    if count == 0:
        print(f"  ABORT: anchor not found for: {patch['label']}")
        print(f"         (file may have changed since this patch was written)")
        return False
    if count > 1:
        print(f"  ABORT: anchor matched {count} times (expected exactly 1) for: {patch['label']}")
        return False

    text = text.replace(patch["anchor"], patch["new"], 1)
    path.write_text(text)
    print(f"  Applied: {patch['label']}")
    return True


def main():
    print("Applying chat auth fixes...")
    ok = True
    for patch in PATCHES:
        if not apply_patch(patch):
            ok = False
            break

    if not ok:
        print("\nOne or more patches could not be applied. No further changes made.")
        sys.exit(1)

    print("\nAll patches applied successfully.")


if __name__ == "__main__":
    main()
