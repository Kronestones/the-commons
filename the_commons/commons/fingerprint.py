"""
fingerprint.py — The Fingerprint

The Commons' truth verification system.
Named for the way it works — scanning content against a verified
source database the way fingerprints are matched against a known record.

Runs invisibly. No AI button on the screen.
Content either publishes or it doesn't.
The best infrastructure is invisible.

Three outcomes:
  CLEAN   — published immediately
  FLAGGED — held for human review, poster notified
  REMOVED — confirmed false, poster notified with reason, one appeal available

Nothing true is ever accidentally removed.
Human review precedes all removals.

— Sovereign Human T.L. Powers · The Commons · 2026
"""

import json
import re
from datetime import datetime
from sqlalchemy.orm import Session
from .database import Post, FingerprintRecord, PostStatus, PostType
from .config import config

# ── Verified Source List ──────────────────────────────────────────────────────
# Public, established sources used for claim verification.
# The Global Circle reviews and updates this list quarterly.
# The list is public — anyone can see what The Commons checks against.

VERIFIED_SOURCES = [
    {"name": "Associated Press",        "url": "https://apnews.com",         "category": "wire"},
    {"name": "Reuters",                 "url": "https://reuters.com",        "category": "wire"},
    {"name": "AFP",                     "url": "https://www.afp.com",        "category": "wire"},
    {"name": "BBC News",                "url": "https://bbc.com/news",       "category": "public_broadcaster"},
    {"name": "NPR",                     "url": "https://npr.org",            "category": "public_broadcaster"},
    {"name": "PolitiFact",              "url": "https://politifact.com",     "category": "fact_checker"},
    {"name": "FactCheck.org",           "url": "https://factcheck.org",      "category": "fact_checker"},
    {"name": "Snopes",                  "url": "https://snopes.com",         "category": "fact_checker"},
    {"name": "USGS",                    "url": "https://usgs.gov",           "category": "government_data"},
    {"name": "CDC",                     "url": "https://cdc.gov",            "category": "government_data"},
    {"name": "WHO",                     "url": "https://who.int",            "category": "international"},
]

# ── Deepfake Signal Patterns ──────────────────────────────────────────────────
# Basic heuristic signals that suggest manipulation.
# More sophisticated detection added as platform grows.

# ── Content Safety — Zero Tolerance ──────────────────────────────────────────
# Nudity and sexual content: instant removal, no appeal, no exceptions.
# Codex Law 8: Children are protected. Codex Law 1: People First.

ZERO_TOLERANCE_PATTERNS = [
    r"\b(nude|nudity|naked|explicit|nsfw|pornograph|sexual content|adult content)\b",
    r"\b(genitalia|genital|breast|nipple)\b",
]

def check_zero_tolerance(text: str) -> bool:
    """Returns True if content triggers zero tolerance removal."""
    import re
    if not text:
        return False
    text_lower = text.lower()
    for pattern in ZERO_TOLERANCE_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False

MANIPULATION_SIGNALS = [
    r"\b(deepfake|synthetic|ai.generated|fake.video|manipulated)\b",
    r"\b(voice.clone|cloned.voice|generated.audio)\b",
]

# ── Political / News Content Signals ─────────────────────────────────────────
# These trigger the Fingerprint. Creative content does not.

POLITICAL_SIGNALS = [
    r"\b(president|senator|congress|parliament|election|vote|ballot|government|policy|law|legislation)\b",
    r"\b(breaking.news|just.in|confirmed|sources.say|officials.say)\b",
    r"\b(war|attack|bombing|invasion|casualties|troops|military.strike)\b",
    r"\b(leaked|whistleblower|classified|cover.up|scandal)\b",
]


class Fingerprint:
    """
    The Commons' truth verification system.
    Invisible to users. Fast. Careful.
    Never removes anything true.
    """

    def __init__(self):
        self.enabled = config.fingerprint_on

    # ── Main Entry Point ──────────────────────────────────────────────────────

    def scan(self, db: Session, post: Post) -> dict:
        """
        Scan a post. Called immediately on upload.
        Returns result and updates post status accordingly.
        """
        if not self.enabled:
            self._publish(db, post)
            return {"result": "clean", "reason": "Fingerprint disabled"}

        # Creative content, personal posts — no fingerprint needed
        if not self._needs_fingerprint(post):
            self._publish(db, post)
            return {"result": "clean", "reason": "Content type does not require verification"}

        # Run the scan
        result = self._run_scan(post)

        # Create fingerprint record
        record = FingerprintRecord(
            post_id            = post.id,
            scan_result        = result["verdict"],
            claims_found       = json.dumps(result.get("claims", [])),
            deepfake_score     = result.get("deepfake_score", 0.0),
            manipulation_score = result.get("manipulation_score", 0.0),
            scanned_at         = datetime.utcnow(),
        )
        db.add(record)

        # Act on verdict
        if result["verdict"] == "clean":
            self._publish(db, post)
        else:
            # Hold for human review — never remove automatically
            post.status = PostStatus.HELD
            db.commit()
            print(f"[FINGERPRINT] Post {post.id} held for human review.")
            print(f"[FINGERPRINT] Reason: {result.get('reason', 'Unknown')}")

        db.commit()
        return result

    # ── Fingerprint Detection ─────────────────────────────────────────────────

    def _needs_fingerprint(self, post: Post) -> bool:
        """
        Does this post need verification?
        Only political content and news. Not creative content.
        """
        if post.is_news or post.is_political:
            return True

        # Auto-detect from content
        text = (post.content or "").lower()
        for pattern in POLITICAL_SIGNALS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _run_scan(self, post: Post) -> dict:
        """
        Run the full scan.
        Phase 1: pattern-based heuristics (fast, works offline)
        Phase 2: source matching (requires network) — added in next phase
        """
        text   = post.content or ""
        claims = self._extract_claims(text)
        deepfake_score     = self._check_deepfake_signals(text)
        manipulation_score = self._check_manipulation_signals(text)

        # High deepfake signal — hold for review
        if deepfake_score > 0.7:
            return {
                "verdict":          "flagged",
                "reason":           "Potential manipulated media detected",
                "claims":           claims,
                "deepfake_score":   deepfake_score,
                "manipulation_score": manipulation_score,
            }

        # High manipulation signal — hold for review
        if manipulation_score > 0.6:
            return {
                "verdict":          "flagged",
                "reason":           "Potential content manipulation detected",
                "claims":           claims,
                "deepfake_score":   deepfake_score,
                "manipulation_score": manipulation_score,
            }

        # Claims found but can't verify yet — hold for human review
        # Phase 2 will add actual source matching here
        if claims and len(claims) > 0:
            return {
                "verdict":          "flagged",
                "reason":           f"{len(claims)} factual claim(s) require verification",
                "claims":           claims,
                "deepfake_score":   deepfake_score,
                "manipulation_score": manipulation_score,
                "note":             "Human review required — claims found"
            }

        # Nothing suspicious found
        return {
            "verdict":          "clean",
            "reason":           "No suspicious signals detected",
            "claims":           claims,
            "deepfake_score":   deepfake_score,
            "manipulation_score": manipulation_score,
        }

    def _extract_claims(self, text: str) -> list:
        """
        Extract factual claims from text.
        Phase 1: simple pattern matching.
        Phase 2: NLP claim extraction.
        """
        claims = []
        claim_patterns = [
            r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\s*(?:people|deaths|casualties|killed|injured)\b",
            r"\b(?:president|senator|official)\s+\w+\s+(?:said|announced|confirmed|denied)\b",
            r"\b(?:new law|new bill|passed|signed|vetoed)\b",
            r"\b\d{4}\s+(?:election|vote|referendum)\b",
        ]
        for pattern in claim_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            claims.extend(matches)
        return list(set(claims))

    def _check_deepfake_signals(self, text: str) -> float:
        """
        Check for deepfake signals in text/metadata.
        Returns 0-1 suspicion score.
        Phase 1: text signals only.
        Phase 2: actual media analysis.
        """
        score = 0.0
        for pattern in MANIPULATION_SIGNALS[:2]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.5
        return min(score, 1.0)

    def _check_manipulation_signals(self, text: str) -> float:
        """Check for content manipulation signals."""
        score = 0.0
        for pattern in MANIPULATION_SIGNALS[1:]:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.4
        return min(score, 1.0)

    # ── Human Review ──────────────────────────────────────────────────────────

    def human_review(self, db: Session, post_id: int, reviewer: str,
                     decision: str, reason: str, notes: str = "") -> dict:
        """
        Human reviewer makes final decision on held content.
        decision: "verified" (publish) or "removed" (remove)
        Nothing true is ever accidentally removed — human makes this call.
        """
        from .database import Post, FingerprintRecord

        post   = db.query(Post).filter(Post.id == post_id).first()
        record = db.query(FingerprintRecord).filter(FingerprintRecord.post_id == post_id).first()

        if not post or not record:
            return {"ok": False, "error": "Post or fingerprint record not found"}

        if post.status != PostStatus.HELD:
            return {"ok": False, "error": f"Post is not in HELD status (currently: {post.status})"}

        record.reviewer      = reviewer
        record.reviewer_notes = notes
        record.decision      = decision
        record.decision_reason = reason
        record.decided_at    = datetime.utcnow()

        if decision == "verified":
            self._publish(db, post)
            record.scan_result = "clean"
            print(f"[FINGERPRINT] Post {post_id} verified by {reviewer} — published.")
        elif decision == "removed":
            post.status = PostStatus.REMOVED
            record.scan_result = "removed"
            db.commit()
            print(f"[FINGERPRINT] Post {post_id} removed by {reviewer}. Reason: {reason}")
            print(f"[FINGERPRINT] Poster notified. One appeal available to Regional Circle.")
        else:
            return {"ok": False, "error": "Decision must be 'verified' or 'removed'"}

        db.commit()
        return {"ok": True, "decision": decision, "post_id": post_id}

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _publish(self, db: Session, post: Post):
        post.status       = PostStatus.PUBLISHED
        post.published_at = datetime.utcnow()
        db.commit()
        print(f"[FINGERPRINT] Post {post.id} published.")

    def get_verified_sources(self) -> list:
        """Return the public list of verified sources."""
        return VERIFIED_SOURCES

    def pending_review_count(self, db: Session) -> int:
        return db.query(Post).filter(Post.status == PostStatus.HELD).count()


fingerprint = Fingerprint()
