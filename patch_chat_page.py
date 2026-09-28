#!/usr/bin/env python3
"""Fix /chat page: script load order, dismiss button, stylesheet, shorter notice."""
import re, sys, shutil

HTML = "templates/chat.html"
JS = "static/js/chat.js"

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

html = read(HTML)
js = read(JS)

if "{% block scripts %}" in html and "chat-disclaimer-short" in html:
    print("chat.html already patched; skipping HTML.")
    html_done = True
else:
    html_done = False

if not html_done:
    new_html = html

    # 1. Shorter subtitle (the welcome line)
    new_html, n = re.subn(
        r'<p class="chat-subtitle">.*?</p>',
        '<p class="chat-subtitle">Welcome to the public chat.</p>',
        new_html, count=1, flags=re.S)
    if n != 1:
        sys.exit("ABORT: subtitle not found")

    # 2. Shorter disclaimer (contains no nested div)
    short = (
        '<div class="chat-disclaimer chat-disclaimer-short" id="chatDisclaimer">\n'
        '    Don\'t share personal information. The Commons isn\'t responsible for what\n'
        '    users say. See something concerning? Tap 🚩 <strong>Report</strong> on that message.\n'
        '    <button class="chat-disclaimer-dismiss" id="dismissDisclaimer" aria-label="Dismiss">Got it</button>\n'
        '  </div>'
    )
    new_html, n = re.subn(
        r'<div class="chat-disclaimer" id="chatDisclaimer">.*?</div>',
        lambda m: short, new_html, count=1, flags=re.S)
    if n != 1:
        sys.exit("ABORT: disclaimer block not found")

    # 3. Link chat.css at the top of the content block
    if "/static/css/chat.css" not in new_html:
        new_html, n = re.subn(
            r'(\{% block content %\}\s*)',
            lambda m: m.group(1) + '<link rel="stylesheet" href="/static/css/chat.css">\n',
            new_html, count=1)
        if n != 1:
            sys.exit("ABORT: content block not found")

    # 4. Move chat.js into the scripts block so it runs AFTER main.js
    new_html, n = re.subn(
        r'\s*<script src="/static/js/chat\.js"></script>\s*\{% endblock %\}\s*$',
        '\n{% endblock %}\n\n{% block scripts %}\n<script src="/static/js/chat.js"></script>\n{% endblock %}\n',
        new_html, count=1)
    if n != 1:
        sys.exit("ABORT: chat.js script tag / final endblock not found")

    shutil.copy(HTML, HTML + ".bak")
    write(HTML, new_html)
    print("patched", HTML)

# JS: make Got it hide the notice directly
ANCHOR = "      disclaimerEl.classList.add('chat-disclaimer-dismissed');"
NEW = ANCHOR + "\n      disclaimerEl.style.display = 'none';"
if "disclaimerEl.style.display = 'none'" in js:
    print("chat.js already patched; skipping JS.")
else:
    if js.count(ANCHOR) != 1:
        sys.exit("ABORT: JS anchor found %d times" % js.count(ANCHOR))
    shutil.copy(JS, JS + ".bak")
    write(JS, js.replace(ANCHOR, NEW))
    print("patched", JS)
