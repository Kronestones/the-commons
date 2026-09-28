#!/usr/bin/env python3
"""Restyle the /chat notice like the feed's 'How The Commons works' box, with an X to close."""
import re, sys, shutil

HTML = "templates/chat.html"
CSS = "static/css/chat.css"
MARK = "chat-notice-v2"

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

NOTICE = '''<div class="chat-disclaimer chat-notice-v2" id="chatDisclaimer">
    <button class="chat-disclaimer-dismiss" id="dismissDisclaimer" aria-label="Close">
      <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/></svg>
    </button>
    <p class="chat-notice-title">ℹ️ Welcome to the public chat</p>
    <p>🔒 Don't share personal information</p>
    <p>⚖️ The Commons isn't responsible for what users say</p>
    <p>🚩 See something concerning? Tap Report on that message</p>
  </div>'''

CSS_ADD = '''
/* chat-notice-v2: matches the feed's "How The Commons works" box */
.chat-disclaimer.chat-notice-v2 {
  position: relative;
  background: #e9f4ee;
  border: 1.5px solid #2d6a4f;
  border-radius: 16px;
  padding: 16px 48px 8px 16px;
  margin: 0 0 16px 0;
  color: #1a1a1a;
}
.chat-notice-v2 p { margin: 0 0 10px 0; line-height: 1.35; }
.chat-notice-v2 .chat-notice-title { font-weight: 700; color: #193a27; font-size: 1.05em; }
.chat-notice-v2 .chat-disclaimer-dismiss {
  position: absolute; top: 10px; right: 10px;
  width: 36px; height: 36px; padding: 0;
  display: flex; align-items: center; justify-content: center;
  background: transparent; border: none; border-radius: 50%;
  color: #161b17; cursor: pointer;
}
'''

html = read(HTML)
css = read(CSS)

if MARK in html:
    print("chat.html already has the new notice; skipping HTML.")
else:
    new = html
    new, n = re.subn(r'<div class="chat-disclaimer[^"]*" id="chatDisclaimer">.*?</div>',
                     lambda m: NOTICE, new, count=1, flags=re.S)
    if n != 1:
        sys.exit("ABORT: notice block not found")
    # welcome is now inside the box, so drop the separate subtitle line
    new = re.sub(r'\s*<p class="chat-subtitle">.*?</p>', '', new, count=1, flags=re.S)
    shutil.copy(HTML, HTML + ".bak2")
    write(HTML, new)
    print("patched", HTML)

if MARK in css:
    print("chat.css already patched; skipping CSS.")
else:
    shutil.copy(CSS, CSS + ".bak2")
    write(CSS, css.rstrip("\n") + "\n" + CSS_ADD)
    print("patched", CSS)
