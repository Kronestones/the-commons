#!/data/data/com.termux/files/usr/bin/bash
# fix_follow_button.sh — Fix follow button calling wrong endpoint (username route
# instead of ID route), causing "User not found" since PROFILE_USER_ID is numeric.
# Run from ~/the_commons

set -e

if [ ! -f "templates/profile.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/profile.html..."
cp templates/profile.html templates/profile.html.bak5
echo "   -> templates/profile.html.bak5"

python3 << 'PYEOF'
path = "templates/profile.html"
with open(path, "r") as f:
    src = f.read()

old = '''async function toggleFollow() {
  const res = await fetch('/api/users/' + PROFILE_USER_ID + '/follow', {
    method: 'POST', headers: { 'Authorization': 'Bearer ' + getProfileToken() }
  });
  const data = await res.json();
  if (data.ok) loadProfile();
}'''

new = '''async function toggleFollow() {
  const res = await fetch('/api/users/' + PROFILE_USER_ID + '/follow_by_id', {
    method: 'POST', headers: { 'Authorization': 'Bearer ' + getProfileToken() }
  });
  const data = await res.json();
  if (data.ok) {
    loadProfile();
  } else {
    showMessage(data.error || 'Could not follow user.', true);
  }
}'''

if old not in src:
    print("❌ Could not find the toggleFollow() function. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/profile.html patched — follow button now calls the correct ID-based endpoint,")
print("   and errors are now shown to the user instead of failing silently.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/profile.html.bak5 templates/profile.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix follow button: use ID-based endpoint instead of username endpoint'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/profile.html.bak5 templates/profile.html"
