#!/data/data/com.termux/files/usr/bin/bash
# fix_member_list_script.sh — Move toggleMemberList() script into {% block scripts %}
# Run from ~/the_commons

set -e

if [ ! -f "templates/sovereign.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/sovereign.html..."
cp templates/sovereign.html templates/sovereign.html.bak2
echo "   -> templates/sovereign.html.bak2"

python3 << 'PYEOF'
path = "templates/sovereign.html"
with open(path, "r") as f:
    src = f.read()

# Remove the stray script we appended last time (dangling outside any block)
stray_script = '''
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

if stray_script not in src:
    print("❌ Could not find the stray script block to remove. Aborting — no changes made.")
    print("   The file may have been edited since. Paste sovereign.html again.")
    raise SystemExit(1)

src = src.replace(stray_script, '', 1)

# Now add it properly inside {% block scripts %}
if '{% block scripts %}' in src:
    # If the block already exists in this template, insert into it
    src = src.replace(
        '{% block scripts %}',
        '''{% block scripts %}
<script>
function toggleMemberList() {
  const dropdown = document.getElementById('member-list-dropdown');
  const arrow = document.getElementById('member-list-arrow');
  const isOpen = dropdown.style.display === 'block';
  dropdown.style.display = isOpen ? 'none' : 'block';
  arrow.textContent = isOpen ? '▼' : '▲';
}
</script>''',
        1
    )
else:
    # No scripts block yet in this template — add one at the end
    src = src.rstrip() + '''

{% block scripts %}
<script>
function toggleMemberList() {
  const dropdown = document.getElementById('member-list-dropdown');
  const arrow = document.getElementById('member-list-arrow');
  const isOpen = dropdown.style.display === 'block';
  dropdown.style.display = isOpen ? 'none' : 'block';
  arrow.textContent = isOpen ? '▼' : '▲';
}
</script>
{% endblock %}
'''

with open(path, "w") as f:
    f.write(src)

print("✅ templates/sovereign.html patched — script now correctly placed in {% block scripts %}.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/sovereign.html.bak2 templates/sovereign.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix member list dropdown script placement'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/sovereign.html.bak2 templates/sovereign.html"
