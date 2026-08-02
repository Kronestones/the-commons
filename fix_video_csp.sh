#!/data/data/com.termux/files/usr/bin/bash
# fix_video_csp.sh — Add media-src to CSP header, which was silently blocking
# all <video> elements from loading Cloudinary content (no media-src directive
# meant it fell back to default-src 'self', blocking the external domain).
# Run from ~/the_commons

set -e

if [ ! -f "commons/security.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up commons/security.py..."
cp commons/security.py commons/security.py.bak
echo "   -> commons/security.py.bak"

python3 << 'PYEOF'
path = "commons/security.py"
with open(path, "r") as f:
    src = f.read()

old = '''        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://res.cloudinary.com; "
            "font-src 'self'; "
            "connect-src 'self';"
        )'''

new = '''        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://res.cloudinary.com; "
            "media-src 'self' https://res.cloudinary.com; "
            "font-src 'self'; "
            "connect-src 'self';"
        )'''

if old not in src:
    print("❌ Could not find the Content-Security-Policy block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ commons/security.py patched — media-src now allows Cloudinary, fixing video playback.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff commons/security.py.bak commons/security.py"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix video playback: add media-src to CSP (was silently blocking all video)'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp commons/security.py.bak commons/security.py"
