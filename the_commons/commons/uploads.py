"""
uploads.py — The Commons Upload System

AI-video-friendly. Every major format supported.
Quality preserved. Large files welcome.

Creators make their videos with whatever tools they love.
The Commons is where they bring them.

Supported video formats:
  MP4, MOV, WebM, AVI, MKV, M4V, FLV, WMV, 3GP

Supported image formats:
  JPG, JPEG, PNG, GIF, WebP, HEIC

Supported audio formats:
  MP3, WAV, AAC, OGG, FLAC, M4A

Max file sizes:
  Video: 2GB (AI-generated video can be large)
  Image: 50MB
  Audio: 500MB

AI Content Disclosure:
  Optional. Creators can tag content as AI-generated.
  Transparent, not punitive. No algorithm penalty.
  Users know what they're watching.

The Fingerprint still applies:
  AI-generated political content is still verified.
  Deepfake detection still runs.
  Ethics don't change based on how content was made.

Codex Law 1: People First — creators deserve great tools.
Codex Law 5: Transparency — AI disclosure is honest, not punitive.
Codex Law 6: Truth — verification applies to all content.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

import os
import uuid
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from .config import config

# ── Supported Formats ─────────────────────────────────────────────────────────

SUPPORTED_VIDEO  = {".mp4", ".mov", ".webm", ".avi", ".mkv",
                    ".m4v", ".flv", ".wmv", ".3gp"}
SUPPORTED_IMAGE  = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}
SUPPORTED_AUDIO  = {".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a"}

MAX_VIDEO_SIZE   = 2 * 1024 * 1024 * 1024   # 2GB
MAX_IMAGE_SIZE   = 50  * 1024 * 1024         # 50MB
MAX_AUDIO_SIZE   = 500 * 1024 * 1024         # 500MB

# ── AI Video Tools ────────────────────────────────────────────────────────────
# Known AI video creation tools — for disclosure tagging

AI_VIDEO_TOOLS = [
    "Runway",
    "Pika",
    "Sora",
    "Stable Video",
    "Midjourney",
    "DALL-E",
    "Adobe Firefly",
    "Synthesia",
    "HeyGen",
    "Descript",
    "CapCut AI",
    "Other AI tool",
]


class UploadManager:

    def get_media_type(self, filename: str) -> Optional[str]:
        """Detect media type from filename extension."""
        ext = Path(filename).suffix.lower()
        if ext in SUPPORTED_VIDEO:
            return "video"
        elif ext in SUPPORTED_IMAGE:
            return "image"
        elif ext in SUPPORTED_AUDIO:
            return "audio"
        return None

    def validate_upload(self, filename: str, file_size: int) -> dict:
        """Validate a file before upload."""
        ext       = Path(filename).suffix.lower()
        media_type = self.get_media_type(filename)

        if not media_type:
            supported = (
                ", ".join(SUPPORTED_VIDEO) + ", " +
                ", ".join(SUPPORTED_IMAGE) + ", " +
                ", ".join(SUPPORTED_AUDIO)
            )
            return {
                "ok":    False,
                "error": f"File type '{ext}' not supported. Supported formats: {supported}"
            }

        # Check file size
        if media_type == "video" and file_size > MAX_VIDEO_SIZE:
            return {"ok": False, "error": "Video files must be under 2GB."}
        elif media_type == "image" and file_size > MAX_IMAGE_SIZE:
            return {"ok": False, "error": "Image files must be under 50MB."}
        elif media_type == "audio" and file_size > MAX_AUDIO_SIZE:
            return {"ok": False, "error": "Audio files must be under 500MB."}

        return {"ok": True, "media_type": media_type, "extension": ext}

    async def save_upload(self, file_data: bytes,
                          filename: str,
                          user_id: int) -> dict:
        """Save an uploaded file to media directory."""
        validation = self.validate_upload(filename, len(file_data))
        if not validation["ok"]:
            return validation

        # Generate unique filename to prevent conflicts
        ext          = Path(filename).suffix.lower()
        unique_name  = f"{user_id}_{uuid.uuid4().hex}{ext}"
        save_path    = config.media_dir / unique_name

        try:
            async with aiofiles.open(save_path, "wb") as f:
                await f.write(file_data)

            return {
                "ok":        True,
                "path":      unique_name,
                "media_type": validation["media_type"],
                "size_bytes": len(file_data),
                "original_name": filename,
            }
        except Exception as e:
            return {"ok": False, "error": f"Upload failed: {str(e)}"}

    def get_ai_tools(self) -> list:
        """Return list of known AI video tools for disclosure."""
        return AI_VIDEO_TOOLS

    def build_ai_disclosure(self, tool_name: str,
                            is_ai_generated: bool) -> dict:
        """
        Build an AI disclosure tag for a post.
        Optional. Transparent. No algorithm penalty.
        """
        if not is_ai_generated:
            return {"is_ai_generated": False}

        return {
            "is_ai_generated": True,
            "tool":            tool_name if tool_name else "AI tool",
            "disclosure_text": f"Made with AI{(' using ' + tool_name) if tool_name else ''}",
            "note":            "Creator disclosed AI generation. Transparent labeling — no penalty applied."
        }

    def get_upload_limits(self) -> dict:
        """Return upload limits for display to users."""
        return {
            "video": {
                "max_size_gb":    2,
                "formats":        list(SUPPORTED_VIDEO),
                "note":           "AI-generated video welcome. Quality preserved."
            },
            "image": {
                "max_size_mb":    50,
                "formats":        list(SUPPORTED_IMAGE),
            },
            "audio": {
                "max_size_mb":    500,
                "formats":        list(SUPPORTED_AUDIO),
            },
            "ai_disclosure": {
                "required":       False,
                "recommended":    True,
                "penalty":        False,
                "note":           "AI disclosure is optional but encouraged. No algorithm penalty for disclosing."
            }
        }


upload_manager = UploadManager()
