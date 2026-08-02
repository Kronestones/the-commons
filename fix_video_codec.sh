#!/data/data/com.termux/files/usr/bin/bash
# fix_video_codec.sh — Force H.264 transcoding for uploaded videos
# Fixes: iPhone videos upload as HEVC (hvc1), which most browsers can't
# play natively, resulting in a broken/black video element.
# Run from ~/the_commons

set -e

if [ ! -f "commons/media_upload.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up commons/media_upload.py..."
cp commons/media_upload.py commons/media_upload.py.bak2
echo "   -> commons/media_upload.py.bak2"

python3 << 'PYEOF'
path = "commons/media_upload.py"
with open(path, "r") as f:
    src = f.read()

old = '''        upload_kwargs = {
            "folder": folder,
            "resource_type": "video" if is_video else "image",
        }
        if not is_video:
            upload_kwargs["quality"] = "auto"
            upload_kwargs["fetch_format"] = "auto"

        result = cloudinary.uploader.upload(file_bytes, **upload_kwargs)'''

new = '''        upload_kwargs = {
            "folder": folder,
            "resource_type": "video" if is_video else "image",
        }
        if not is_video:
            upload_kwargs["quality"] = "auto"
            upload_kwargs["fetch_format"] = "auto"
        else:
            # Force H.264 — many phones (especially iPhone) record in HEVC
            # (hvc1), which most browsers cannot play natively in <video>.
            # Transcoding to H.264 here guarantees universal playback.
            upload_kwargs["eager"] = [
                {"video_codec": "h264", "quality": "auto"}
            ]
            upload_kwargs["eager_async"] = False

        result = cloudinary.uploader.upload(file_bytes, **upload_kwargs)

        # If we requested an eager H.264 transformation, use that URL —
        # it's guaranteed browser-playable, unlike the raw uploaded file.
        if is_video and result.get("eager"):
            result["secure_url"] = result["eager"][0]["secure_url"]'''

if old not in src:
    print("❌ Could not find the upload_kwargs block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ commons/media_upload.py patched — videos now transcoded to H.264 for universal playback.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff commons/media_upload.py.bak2 commons/media_upload.py"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix video playback: transcode to H.264 (was serving HEVC from iPhones)'"
echo "   git push"
echo ""
echo "NOTE: eager_async=False makes the upload wait for transcoding to finish"
echo "before returning — slightly slower upload, but guarantees the URL works"
echo "immediately rather than pointing at a still-processing file."
echo ""
echo "If something looks wrong, restore with:"
echo "   cp commons/media_upload.py.bak2 commons/media_upload.py"
