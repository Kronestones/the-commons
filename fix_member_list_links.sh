#!/data/data/com.termux/files/usr/bin/bash
# fix_member_list_links.sh — Make member list usernames clickable, linking to /profile/{username}
# Run from ~/the_commons

set -e

if [ ! -f "templates/sovereign.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/sovereign.html..."
cp templates/sovereign.html templates/sovereign.html.bak3
echo "   -> templates/sovereign.html.bak3"

python3 << 'PYEOF'
path = "templates/sovereign.html"
with open(path, "r") as f:
    src = f.read()

old = '''        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-bottom:1px solid var(--border);font-size:14px;">
          <span>@{{ m.username }}{% if m.role.value == 'sovereign' %} 👑{% elif m.role.value == 'circle' %} ⭐{% endif %}</span>
          <span style="font-size:12px;color:var(--muted);">{{ m.created_at.strftime("%b %Y") }}</span>
        </div>'''

new = '''        <a href="/profile/{{ m.username }}" style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-bottom:1px solid var(--border);font-size:14px;text-decoration:none;color:inherit;">
          <span>@{{ m.username }}{% if m.role.value == 'sovereign' %} 👑{% elif m.role.value == 'circle' %} ⭐{% endif %}</span>
          <span style="font-size:12px;color:var(--muted);">{{ m.created_at.strftime("%b %Y") }}</span>
        </a>'''

if old not in src:
    print("❌ Could not find the member row block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/sovereign.html patched — member usernames now link to their profile pages.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/sovereign.html.bak3 templates/sovereign.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Link member list usernames to profile pages'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/sovereign.html.bak3 templates/sovereign.html"
