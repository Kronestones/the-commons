#!/data/data/com.termux/files/usr/bin/bash
# fix_messages_header.sh — Replace messages.html header with a visible close/back bar
# Run from ~/the_commons

set -e

if [ ! -f "templates/messages.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/messages.html..."
cp templates/messages.html templates/messages.html.bak3
echo "   -> templates/messages.html.bak3"

python3 << 'PYEOF'
path = "templates/messages.html"
with open(path, "r") as f:
    src = f.read()

old_header = '''  <header class="site-header">
    <div class="header-inner">
      <span class="site-title">The Commons</span>
      <nav class="nav-links" id="nav-links">
        <a href="/">Feed</a>
        <a href="/messages" class="active">Messages</a>
      </nav>
    </div>
  </header>'''

new_header = '''  <header style="background:var(--green-dark, #1a4a2e);color:white;padding:14px 16px;display:flex;align-items:center;gap:12px;">
    <a href="/" style="color:white;text-decoration:none;font-size:22px;line-height:1;display:flex;align-items:center;" aria-label="Close messages">✕</a>
    <span style="font-weight:600;font-size:17px;">Messages</span>
  </header>'''

if old_header not in src:
    print("❌ Could not find the existing header block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old_header, new_header, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/messages.html patched — header replaced with visible ✕ close bar.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/messages.html.bak3 templates/messages.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Add visible close header to messages page'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/messages.html.bak3 templates/messages.html"
