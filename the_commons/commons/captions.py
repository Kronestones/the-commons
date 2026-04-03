"""
captions.py — Closed Captions

Auto-generated captions for video content.
Accessibility first. No extra cost to creators.

Uses faster-whisper — free, open source, runs locally.
No audio sent to external servers.
Privacy by design.

Captions are generated when video is uploaded.
Stored with the post. Available to all viewers.
Can be toggled on/off by the viewer.

Codex Law 1: People First — accessibility matters.
Codex Law 3: No data selling — audio never leaves the platform.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

import os
import json
from datetime import datetime
from pathlib import Path
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Session
from .database import Base


class Caption(Base):
    """Stored captions for a video post."""
    __tablename__ = "captions"

    id              = Column(Integer, primary_key=True, index=True)
    post_id         = Column(Integer, ForeignKey("posts.id"), unique=True)
    language        = Column(String(10), default="en")
    caption_data    = Column(Text, default="[]")  # JSON array of {start, end, text}
    generated_at    = Column(DateTime, default=datetime.utcnow)
    is_auto         = Column(Boolean, default=True)   # Auto-generated vs manually added


class CaptionManager:

    def get_captions(self, db: Session, post_id: int) -> dict:
        """Get captions for a post."""
        caption = db.query(Caption).filter(Caption.post_id == post_id).first()
        if not caption:
            return {"ok": False, "error": "No captions available for this post."}

        try:
            segments = json.loads(caption.caption_data)
        except Exception:
            segments = []

        return {
            "ok":           True,
            "post_id":      post_id,
            "language":     caption.language,
            "segments":     segments,
            "is_auto":      caption.is_auto,
            "generated_at": caption.generated_at.isoformat(),
        }

    def add_captions(self, db: Session, post_id: int,
                     segments: list, language: str = "en",
                     is_auto: bool = True) -> dict:
        """Store captions for a post."""
        existing = db.query(Caption).filter(Caption.post_id == post_id).first()

        if existing:
            existing.caption_data = json.dumps(segments)
            existing.language     = language
            existing.generated_at = datetime.utcnow()
        else:
            caption = Caption(
                post_id      = post_id,
                language     = language,
                caption_data = json.dumps(segments),
                is_auto      = is_auto,
            )
            db.add(caption)

        db.commit()
        return {"ok": True, "message": "Captions saved."}

    def generate_captions(self, audio_path: str,
                          post_id: int, db: Session) -> dict:
        """
        Generate captions from audio using faster-whisper.
        Falls back gracefully if whisper not installed.
        """
        try:
            from faster_whisper import WhisperModel

            print(f"[CAPTIONS] Generating captions for post {post_id}...")
            model    = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_path, beam_size=5)

            caption_segments = []
            for segment in segments:
                caption_segments.append({
                    "start": round(segment.start, 2),
                    "end":   round(segment.end, 2),
                    "text":  segment.text.strip(),
                })

            result = self.add_captions(db, post_id, caption_segments,
                                       language=info.language)
            print(f"[CAPTIONS] Generated {len(caption_segments)} segments for post {post_id}")
            return result

        except ImportError:
            # faster-whisper not installed — note it but don't crash
            print("[CAPTIONS] faster-whisper not installed — captions unavailable")
            return {
                "ok":    False,
                "error": "Caption generation unavailable. Install faster-whisper to enable."
            }
        except Exception as e:
            print(f"[CAPTIONS] Error generating captions: {e}")
            return {"ok": False, "error": str(e)}

    def delete_captions(self, db: Session, post_id: int) -> dict:
        """Remove captions for a post."""
        caption = db.query(Caption).filter(Caption.post_id == post_id).first()
        if caption:
            db.delete(caption)
            db.commit()
        return {"ok": True}


caption_manager = CaptionManager()
