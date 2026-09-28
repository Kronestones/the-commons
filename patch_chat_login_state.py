#!/usr/bin/env python3
"""/chat: treat a user as logged in when they have a token, not only when localStorage has 'username'.
(Only register.html saves 'username'; normal login doesn't, so chat.js thought everyone was logged out.)"""
import sys, shutil

JS = "static/js/chat.js"
with open(JS, encoding="utf-8") as f:
    js = f.read()

if "IS_LOGGED_IN" in js:
    print("chat.js already patched.")
    sys.exit(0)

EDITS = [
    ("  const AUTH_TOKEN = (typeof getToken === 'function') ? getToken() : null;",
     "  const AUTH_TOKEN = (typeof getToken === 'function') ? getToken() : null;\n"
     "  const IS_LOGGED_IN = !!(AUTH_TOKEN || CURRENT_USERNAME);"),
    ("  if (CURRENT_USERNAME) {\n    if (chatInputLoggedIn)",
     "  if (IS_LOGGED_IN) {\n    if (chatInputLoggedIn)"),
    ("if (msg.is_self || !CURRENT_USERNAME) {",
     "if (msg.is_self || !IS_LOGGED_IN) {"),
]
for old, new in EDITS:
    if js.count(old) != 1:
        sys.exit("ABORT: anchor found %d times:\n%s" % (js.count(old), old))
    js = js.replace(old, new)

shutil.copy(JS, JS + ".bak4")
with open(JS, "w", encoding="utf-8") as f:
    f.write(js)
print("patched", JS)
