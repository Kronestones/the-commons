#!/data/data/com.termux/files/usr/bin/bash
# fix_banner.sh — The Commons banner upload button fix
# Fixes: "Edit Banner" label not receiving taps due to overflow:hidden ancestor
# Run from ~/the_commons

set -e

if [ ! -f "templates/profile.html" ]; then
    echo "❌ Run this from the_commons project root (templates/profile.html not found here)."
    exit 1
fi

echo "📦 Backing up templates/profile.html..."
cp templates/profile.html templates/profile.html.bak2
echo "   -> templates/profile.html.bak2"

python3 << 'PYEOF'
path = "templates/profile.html"
with open(path, "r") as f:
    src = f.read()

old_banner = '''  <!-- Banner -->
  <div class="profile-banner" id="profile-banner" style="height:160px;background:var(--green-dark);border-radius:12px;margin-bottom:-40px;position:relative;overflow:hidden;">
    <img id="banner-img" src="" alt="" style="width:100%;height:100%;object-fit:cover;display:none;">
    <label id="banner-upload-btn" style="display:none;position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.5);color:white;padding:6px 12px;border-radius:8px;cursor:pointer;font-size:12px;">
      📷 Edit Banner
      <input type="file" accept="image/*" style="display:none" onchange="uploadBanner(this)">
    </label>
  </div>'''

new_banner = '''  <!-- Banner -->
  <div id="profile-banner-wrap" style="position:relative;margin-bottom:-40px;">
    <div class="profile-banner" id="profile-banner" style="height:160px;background:var(--green-dark);border-radius:12px;overflow:hidden;">
      <img id="banner-img" src="" alt="" style="width:100%;height:100%;object-fit:cover;display:none;">
    </div>
    <label id="banner-upload-btn" style="display:none;position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.5);color:white;padding:6px 12px;border-radius:8px;cursor:pointer;font-size:12px;z-index:10;">
      📷 Edit Banner
      <input type="file" accept="image/*" style="display:none" onchange="uploadBanner(this)">
    </label>
  </div>'''

if old_banner not in src:
    print("❌ Could not find the exact banner block in profile.html.")
    print("   The file may have changed since last review. Aborting —")
    print("   no changes made. Paste profile.html again and I'll hand-patch it.")
    raise SystemExit(1)

src = src.replace(old_banner, new_banner, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/profile.html patched — banner label moved outside overflow:hidden container.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/profile.html.bak2 templates/profile.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix banner upload button hit target'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/profile.html.bak2 templates/profile.html"
