#!/data/data/com.termux/files/usr/bin/bash
# fix_member_list.sh — Add scrollable member dropdown to Sovereign Dashboard
# Run from ~/the_commons

set -e

if [ ! -f "main.py" ] || [ ! -f "templates/sovereign.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up files..."
cp main.py main.py.bak3
cp templates/sovereign.html templates/sovereign.html.bak
echo "   -> main.py.bak3"
echo "   -> templates/sovereign.html.bak"

# ── Patch main.py: query full member list ──────────────────────────────────
python3 << 'PYEOF'
path = "main.py"
with open(path, "r") as f:
    src = f.read()

old = '''    # Platform stats
    total_members = db.query(User).filter(User.is_active == True).count()
    total_posts   = db.query(Post).filter(Post.status == PostStatus.PUBLISHED).count()
    pending_posts = db.query(Post).filter(Post.status == PostStatus.PENDING).count()'''

new = '''    # Platform stats
    member_list = (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.created_at.desc())
        .all()
    )
    total_members = len(member_list)
    total_posts   = db.query(Post).filter(Post.status == PostStatus.PUBLISHED).count()
    pending_posts = db.query(Post).filter(Post.status == PostStatus.PENDING).count()'''

if old not in src:
    print("❌ Could not find the platform stats block in main.py. Aborting.")
    raise SystemExit(1)
src = src.replace(old, new, 1)

old_return = '''    return templates.TemplateResponse("sovereign.html", {
        "request":          request,
        "current_user":     current_user,
        "total_members":    total_members,'''

new_return = '''    return templates.TemplateResponse("sovereign.html", {
        "request":          request,
        "current_user":     current_user,
        "total_members":    total_members,
        "member_list":      member_list,'''

if old_return not in src:
    print("❌ Could not find the sovereign.html TemplateResponse block in main.py. Aborting.")
    raise SystemExit(1)
src = src.replace(old_return, new_return, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ main.py patched — member_list now passed to sovereign.html.")
PYEOF

# ── Patch templates/sovereign.html: dropdown UI ────────────────────────────
python3 << 'PYEOF'
path = "templates/sovereign.html"
with open(path, "r") as f:
    src = f.read()

old = '''      <div style="display:flex;justify-content:space-between;">
        <span>Active members</span>
        <strong>{{ total_members }}</strong>
      </div>'''

new = '''      <div style="display:flex;justify-content:space-between;align-items:center;cursor:pointer;" onclick="toggleMemberList()">
        <span>Active members</span>
        <strong>{{ total_members }} <span id="member-list-arrow" style="font-size:12px;">▼</span></strong>
      </div>
      <div id="member-list-dropdown" style="display:none;max-height:240px;overflow-y:auto;border:1px solid var(--border);border-radius:8px;margin-top:4px;">
        {% for m in member_list %}
        <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;border-bottom:1px solid var(--border);font-size:14px;">
          <span>@{{ m.username }}{% if m.role.value == 'sovereign' %} 👑{% elif m.role.value == 'circle' %} ⭐{% endif %}</span>
          <span style="font-size:12px;color:var(--muted);">{{ m.created_at.strftime("%b %Y") }}</span>
        </div>
        {% endfor %}
      </div>'''

if old not in src:
    print("❌ Could not find the Active members block in sovereign.html. Aborting.")
    raise SystemExit(1)
src = src.replace(old, new, 1)

# Add the toggle script — insert before closing </body> if present, else append
script = '''
<script>
function toggleMemberList() {
  const dropdown = document.getElementById('member-list-dropdown');
  const arrow = document.getElementById('member-list-arrow');
  const isOpen = dropdown.style.display === 'block';
  dropdown.style.display = isOpen ? 'none' : 'block';
  arrow.textContent = isOpen ? '▼' : '▲';
}
</script>
'''

if '</body>' in src:
    src = src.replace('</body>', script + '</body>', 1)
else:
    src = src + script

with open(path, "w") as f:
    f.write(src)

print("✅ templates/sovereign.html patched — scrollable member dropdown added.")
PYEOF

echo ""
echo "🎉 Done. Review the diffs with:"
echo "   diff main.py.bak3 main.py"
echo "   diff templates/sovereign.html.bak templates/sovereign.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Add scrollable member list to Sovereign Dashboard'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp main.py.bak3 main.py"
echo "   cp templates/sovereign.html.bak templates/sovereign.html"
