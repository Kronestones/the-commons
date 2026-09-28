#!/usr/bin/env python3
"""Fix chat send/read: server returned an unserializable DB object (500), field names
didn't match what chat.js reads (empty bubbles), block sent the wrong param, UTC times
were shown as local, and stored HTML entities showed literally."""
import sys, shutil

JS = "static/js/chat.js"
PY = "commons/chat.py"
HTML = "templates/chat.html"

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

js, py = read(JS), read(PY)

JS_EDITS = [
    ("el.dataset.username = msg.username;", "el.dataset.username = msg.author;"),
    ("usernameEl.textContent = msg.username;", "usernameEl.textContent = msg.author;"),
    ("querySelector('.chat-message-text').textContent = msg.message;",
     "querySelector('.chat-message-text').textContent = decodeEntities(msg.content);"),
    ("reportMessage(msg.id, msg.username)", "reportMessage(msg.id, msg.author)"),
    ("blockUser(msg.username)", "blockUser(msg.author_id, msg.author)"),
    ("async function blockUser(username) {", "async function blockUser(userId, username) {"),
    ("formData.append('blocked_username', username);", "formData.append('blocked_id', userId);"),
    ("  function escapeForDisplay(str) {",
     "  function decodeEntities(str) {\n"
     "    // Server stores messages HTML-escaped (e.g. don&#x27;t); turn them back into\n"
     "    // plain text. A textarea never runs scripts, and the result is only ever\n"
     "    // assigned via textContent, so this stays safe.\n"
     "    const t = document.createElement('textarea');\n"
     "    t.innerHTML = str == null ? '' : String(str);\n"
     "    return t.value;\n"
     "  }\n\n"
     "  function escapeForDisplay(str) {"),
    ("    // Immediately fetch so the sender sees their own message right away",
     "    const sent = await res.json().catch(() => ({}));\n"
     "    if (sent && sent.ok === false) {\n"
     "      throw new Error(sent.error || 'Could not send message.');\n"
     "    }\n\n"
     "    // Immediately fetch so the sender sees their own message right away"),
]
PY_EDITS = [
    ('return {"ok": True, "message": chat_message}', 'return {"ok": True, "id": chat_message.id}', True),
    ('"created_at": m.created_at.isoformat(),', '"created_at": m.created_at.isoformat() + "Z",', False),
]

new_js, new_py = js, py

if "decodeEntities" in js:
    print("chat.js already patched; skipping.")
    new_js = None
else:
    for old, new in JS_EDITS:
        if new_js.count(old) != 1:
            sys.exit("ABORT (chat.js): anchor found %d times:\n%s" % (new_js.count(old), old))
        new_js = new_js.replace(old, new)

if '"id": chat_message.id}' in py:
    print("chat.py already patched; skipping.")
    new_py = None
else:
    for old, new, must_be_one in PY_EDITS:
        c = new_py.count(old)
        if c == 0 or (must_be_one and c != 1):
            sys.exit("ABORT (chat.py): anchor found %d times:\n%s" % (c, old))
        new_py = new_py.replace(old, new)

# everything checked; now write
if new_js is not None:
    shutil.copy(JS, JS + ".bak5"); write(JS, new_js); print("patched", JS)
if new_py is not None:
    shutil.copy(PY, PY + ".bak5"); write(PY, new_py); print("patched", PY)

# bump cache-buster so phones fetch the new chat.js
try:
    h = read(HTML)
    if "chat.js?v=3" in h:
        write(HTML, h.replace("chat.js?v=3", "chat.js?v=4")); print("bumped chat.js cache version")
except FileNotFoundError:
    pass
