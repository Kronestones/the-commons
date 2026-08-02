#!/data/data/com.termux/files/usr/bin/bash
# fix_feed_video_render.sh — Add video-aware rendering to the initial
# server-rendered feed (templates/index.html), which was hardcoded to <img>
# and missed when we patched the JS infinite-scroll rendering earlier.
# Run from ~/the_commons

set -e

if [ ! -f "templates/index.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/index.html..."
cp templates/index.html templates/index.html.bak2
echo "   -> templates/index.html.bak2"

python3 << 'PYEOF'
path = "templates/index.html"
with open(path, "r") as f:
    src = f.read()

old = '''        {% if post.media_path %}
        <img src="{{ post.media_path if post.media_path.startswith('http') else '/media/' + post.media_path }}" style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;object-fit:cover;">
        {% endif %}'''

new = '''        {% if post.media_path %}
          {% if post.post_type.value == 'video' %}
        <video src="{{ post.media_path if post.media_path.startswith('http') else '/media/' + post.media_path }}" controls playsinline style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;background:#000;"></video>
          {% else %}
        <img src="{{ post.media_path if post.media_path.startswith('http') else '/media/' + post.media_path }}" style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;object-fit:cover;">
          {% endif %}
        {% endif %}'''

if old not in src:
    print("❌ Could not find the media_path block in index.html. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/index.html patched — initial feed load now renders <video> for video posts.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/index.html.bak2 templates/index.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix feed: render video posts correctly on initial page load (Jinja template missed)'"
echo "   git push"
echo ""
echo "NOTE: this assumes post.post_type is a Python enum with a .value attribute"
echo "(matching how post_type is used elsewhere in this same template)."
echo "If it errors after deploy, post_type might be a plain string instead —"
echo "let me know and we'll adjust to post.post_type == 'video' without .value."
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/index.html.bak2 templates/index.html"
