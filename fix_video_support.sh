#!/data/data/com.termux/files/usr/bin/bash
# fix_video_support.sh — Add video upload (Cloudinary) and playback support
# Fixes: media_upload.py hardcoded to image-only resource_type,
# and post rendering only ever showing <img>, never <video>.
# Run from ~/the_commons

set -e

if [ ! -f "commons/media_upload.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up files..."
cp commons/media_upload.py commons/media_upload.py.bak
cp main.py main.py.bak6
cp static/js/main.js static/js/main.js.bak2
cp templates/profile.html templates/profile.html.bak6
echo "   Backed up: media_upload.py, main.py, main.js, profile.html"

python3 << 'PYEOF'
path = "commons/media_upload.py"
with open(path, "r") as f:
    src = f.read()

old = '''def upload_image(file_bytes: bytes, folder: str = "the_commons") -> dict:
    """Upload image to Cloudinary. Returns url and public_id."""
    init_cloudinary()
    try:
        result = cloudinary.uploader.upload(
            file_bytes,
            folder       = folder,
            resource_type = "image",
            quality      = "auto",
            fetch_format = "auto",
        )
        return {
            "ok":        True,
            "url":       result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        print(f"[CLOUDINARY] Upload error: {e}")
        return {"ok": False, "error": str(e)}'''

new = '''def upload_image(file_bytes: bytes, folder: str = "the_commons",
                 is_video: bool = False) -> dict:
    """
    Upload media to Cloudinary. Returns url and public_id.
    Set is_video=True for video files — Cloudinary requires a different
    resource_type for video vs image uploads, and this was previously
    hardcoded to "image", which silently broke video uploads.
    """
    init_cloudinary()
    try:
        upload_kwargs = {
            "folder": folder,
            "resource_type": "video" if is_video else "image",
        }
        if not is_video:
            upload_kwargs["quality"] = "auto"
            upload_kwargs["fetch_format"] = "auto"

        result = cloudinary.uploader.upload(file_bytes, **upload_kwargs)
        return {
            "ok":        True,
            "url":       result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        print(f"[CLOUDINARY] Upload error: {e}")
        return {"ok": False, "error": str(e)}'''

if old not in src:
    print("❌ Could not find upload_image() in media_upload.py. Aborting.")
    raise SystemExit(1)
src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ commons/media_upload.py patched — now supports both image and video uploads.")
PYEOF

python3 << 'PYEOF'
path = "main.py"
with open(path, "r") as f:
    src = f.read()

old_call = '''    media_url = ""
    if media and media.filename:
        from commons.media_upload import upload_image
        file_bytes = await media.read()
        upload = upload_image(file_bytes, folder="posts")
        if upload["ok"]:
            media_url = upload["url"]'''

new_call = '''    media_url = ""
    if media and media.filename:
        from commons.media_upload import upload_image
        file_bytes = await media.read()
        is_video = (media.content_type or "").startswith("video/")
        upload = upload_image(file_bytes, folder="posts", is_video=is_video)
        if upload["ok"]:
            media_url = upload["url"]'''

count = src.count(old_call)
if count == 0:
    print("❌ Could not find the posts upload_image call in main.py. Aborting this part.")
else:
    src = src.replace(old_call, new_call)
    print(f"✅ main.py patched — {count} post-upload call site(s) now detect video files.")

with open(path, "w") as f:
    f.write(src)
PYEOF

python3 << 'PYEOF'
path = "static/js/main.js"
with open(path, "r") as f:
    src = f.read()

old = '''        ${post.media_path ? `<img src="${post.media_path.startsWith('http') ? post.media_path : '/media/' + post.media_path}" style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;object-fit:cover;">` : ''}'''

new = '''        ${post.media_path ? (
          post.post_type === 'video'
            ? `<video src="${post.media_path.startsWith('http') ? post.media_path : '/media/' + post.media_path}" controls playsinline style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;background:#000;"></video>`
            : `<img src="${post.media_path.startsWith('http') ? post.media_path : '/media/' + post.media_path}" style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;object-fit:cover;">`
        ) : ''}'''

if old not in src:
    print("❌ Could not find the feed media rendering line in main.js. Aborting this part.")
else:
    src = src.replace(old, new, 1)
    print("✅ static/js/main.js patched — feed now renders <video> for video posts.")

with open(path, "w") as f:
    f.write(src)
PYEOF

python3 << 'PYEOF'
path = "templates/profile.html"
with open(path, "r") as f:
    src = f.read()

old = '''        ${post.media_path ? `<img src="${post.media_path.startsWith('http') ? post.media_path : '/media/' + post.media_path}" style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;object-fit:cover;">` : ''}'''

new = '''        ${post.media_path ? (
          post.post_type === 'video'
            ? `<video src="${post.media_path.startsWith('http') ? post.media_path : '/media/' + post.media_path}" controls playsinline style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;background:#000;"></video>`
            : `<img src="${post.media_path.startsWith('http') ? post.media_path : '/media/' + post.media_path}" style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;object-fit:cover;">`
        ) : ''}'''

if old not in src:
    print("❌ Could not find the profile media rendering line in profile.html. Aborting this part.")
else:
    src = src.replace(old, new, 1)
    print("✅ templates/profile.html patched — profile now renders <video> for video posts.")

with open(path, "w") as f:
    f.write(src)
PYEOF

echo ""
echo "🎉 Done. Review the diffs with:"
echo "   diff commons/media_upload.py.bak commons/media_upload.py"
echo "   diff main.py.bak6 main.py"
echo "   diff static/js/main.js.bak2 static/js/main.js"
echo "   diff templates/profile.html.bak6 templates/profile.html"
echo ""
echo "If everything looks right:"
echo "   git add -A && git commit -m 'Add video upload and playback support (image-only Cloudinary bug)'"
echo "   git push"
echo ""
echo "If something looks wrong, restore any file with:"
echo "   cp <file>.bak <file>   (or main.py.bak6 for main.py)"
