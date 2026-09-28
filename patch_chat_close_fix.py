#!/usr/bin/env python3
"""Make the chat notice close button work no matter what is cached or which JS runs."""
import re, sys, shutil

HTML = "templates/chat.html"
CSS = "static/css/chat.css"
ONCLICK = "onclick=\"document.getElementById('chatDisclaimer').style.display='none'\""
VER = "v=3"

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

html = read(HTML)
new = html
changed = False

# 1. inline close handler on the dismiss button (independent of chat.js / chat.css)
if ONCLICK not in new:
    new, n = re.subn(r'<button class="chat-disclaimer-dismiss" id="dismissDisclaimer"',
                     lambda m: m.group(0) + ' type="button" ' + ONCLICK, new, count=1)
    if n != 1:
        sys.exit("ABORT: dismiss button not found")
    changed = True

# 2. cache-bust chat.js and chat.css so phones fetch the new files
for path in ("/static/js/chat.js", "/static/css/chat.css"):
    if path + "?" + VER not in new:
        new, n = re.subn(re.escape(path) + r'(\?[^"]*)?"', path + "?" + VER + '"', new, count=1)
        if n != 1:
            sys.exit("ABORT: %s reference not found" % path)
        changed = True

if changed:
    shutil.copy(HTML, HTML + ".bak3")
    write(HTML, new)
    print("patched", HTML)
else:
    print("chat.html already patched.")

# 3. CSS: dismissed state always hides; shorter message window on phones so the input row is visible
css = read(CSS)
ADD = ""
RULE = ".chat-disclaimer-dismissed { display: none !important; }"
if RULE not in css:
    ADD += "\n/* close fix */\n" + RULE + "\n"
MOBILE_MARK = "chat-window-mobile-v3"
if MOBILE_MARK not in css:
    ADD += ("\n/* chat-window-mobile-v3: keep the message box + input on one screen */\n"
            "@media (max-width: 600px) {\n"
            "  .chat-window { height: 42vh; min-height: 220px; }\n"
            "}\n")
if ADD:
    shutil.copy(CSS, CSS + ".bak3")
    write(CSS, css.rstrip("\n") + "\n" + ADD)
    print("patched", CSS)
else:
    print("chat.css already patched.")
