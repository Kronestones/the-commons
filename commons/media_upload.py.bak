"""
media_upload.py — Cloudinary image uploads

All media stored on Cloudinary — persists across Render restarts.
"""
import cloudinary
import cloudinary.uploader
from .config import config


def init_cloudinary():
    cloudinary.config(
        cloud_name = config.cloudinary_cloud,
        api_key    = config.cloudinary_api_key,
        api_secret = config.cloudinary_api_secret,
        secure     = True
    )


def upload_image(file_bytes: bytes, folder: str = "the_commons") -> dict:
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
        return {"ok": False, "error": str(e)}
