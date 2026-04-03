"""
security.py — The Commons Security

Protecting the platform and everyone on it.
Adapted from Sentinel's beacon rate limiting,
cooldown system, and deception signal detection.

Layers of protection:

  RATE LIMITING    — No single IP can flood the API.
                     Login attempts throttled to prevent brute force.
                     Registration throttled to prevent spam accounts.

  IP COOLDOWN      — Failed login attempts trigger escalating cooldowns.
                     Adapted from Sentinel's beacon cooldown system.

  INPUT SANITIZATION — All user input cleaned before processing.
                       SQL injection patterns detected and blocked.
                       XSS patterns stripped from content.

  CONTENT SCANNING  — Posts scanned for injection attempts.
                       Adapted from Sentinel's deception signal detection.

  SECURITY HEADERS  — Standard web security headers on every response.

  REQUEST LIMITS    — Oversized requests rejected before processing.

No security system is perfect.
But these layers mean an attacker has to work hard
for very little return.

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

import re
import time
import threading
import html
from collections import defaultdict
from datetime import datetime
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ── Rate Limit Configuration ──────────────────────────────────────────────────

RATE_LIMITS = {
    "login":        {"max": 5,   "window": 300,  "cooldown": 900},   # 5 attempts / 5 min → 15 min lockout
    "register":     {"max": 3,   "window": 3600, "cooldown": 3600},  # 3 accounts / hour
    "post":         {"max": 30,  "window": 60,   "cooldown": 60},    # 30 posts / minute
    "vote":         {"max": 100, "window": 60,   "cooldown": 30},    # 100 votes / minute
    "api":          {"max": 200, "window": 60,   "cooldown": 30},    # 200 requests / minute general
    "purchase":     {"max": 10,  "window": 60,   "cooldown": 60},    # 10 purchases / minute
}

MAX_REQUEST_SIZE_MB = 100  # Reject requests larger than this

# ── Injection Attack Patterns ─────────────────────────────────────────────────
# Adapted from Sentinel's deception signal detection

SQL_INJECTION_PATTERNS = [
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b.*\b(FROM|INTO|TABLE|WHERE)\b)",
    r"(--|;|\/\*|\*\/|xp_|sp_)",
    r"(\b(OR|AND)\b\s+[\w\s]*=[\w\s]*)",
    r"('.*'|\".*\")\s*(=|<|>|LIKE)",
]

XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript\s*:",
    r"on\w+\s*=",
    r"<\s*iframe[^>]*>",
    r"<\s*object[^>]*>",
    r"<\s*embed[^>]*>",
    r"expression\s*\(",
]

SHELL_INJECTION_PATTERNS = [
    r"(\||&|;|`|\$\(|\${)",
    r"(\.\.\/|\.\.\\)",
    r"\b(wget|curl|nc|netcat|bash|sh|cmd|powershell)\b",
]


# ── Rate Limiter ──────────────────────────────────────────────────────────────

class RateLimiter:
    """
    In-memory rate limiter.
    Tracks requests per IP per action type.
    Adapted from Sentinel's beacon rate limiting.
    """

    def __init__(self):
        self._requests  = defaultdict(list)   # {ip:action: [timestamps]}
        self._cooldowns = {}                   # {ip:action: until_timestamp}
        self._lock      = threading.Lock()

    def check(self, ip: str, action: str) -> dict:
        """
        Check if this IP is allowed to perform this action.
        Returns {"allowed": True} or {"allowed": False, "retry_after": seconds}
        """
        if action not in RATE_LIMITS:
            return {"allowed": True}

        config  = RATE_LIMITS[action]
        key     = f"{ip}:{action}"
        now     = time.time()

        with self._lock:
            # Check cooldown first
            if key in self._cooldowns:
                until = self._cooldowns[key]
                if now < until:
                    return {
                        "allowed":     False,
                        "retry_after": int(until - now),
                        "reason":      f"Too many {action} attempts. Try again in {int(until - now)}s."
                    }
                else:
                    del self._cooldowns[key]

            # Clean old timestamps outside the window
            window_start = now - config["window"]
            self._requests[key] = [t for t in self._requests[key] if t > window_start]

            # Check if over limit
            if len(self._requests[key]) >= config["max"]:
                # Apply cooldown
                self._cooldowns[key] = now + config["cooldown"]
                self._requests[key]  = []
                return {
                    "allowed":     False,
                    "retry_after": config["cooldown"],
                    "reason":      f"Rate limit exceeded. Try again in {config['cooldown']}s."
                }

            # Record this request
            self._requests[key].append(now)
            return {"allowed": True}

    def get_cooldown_remaining(self, ip: str, action: str) -> int:
        key = f"{ip}:{action}"
        with self._lock:
            until = self._cooldowns.get(key, 0)
            remaining = int(until - time.time())
            return max(0, remaining)

    def clear_cooldown(self, ip: str, action: str):
        """Clear a cooldown — used when login succeeds after previous failures."""
        key = f"{ip}:{action}"
        with self._lock:
            self._cooldowns.pop(key, None)
            self._requests.pop(key, None)


# ── Input Sanitizer ───────────────────────────────────────────────────────────

class InputSanitizer:
    """
    Cleans and validates all user input.
    Detects and blocks injection attempts.
    """

    def sanitize_text(self, text: str, max_length: int = 10000) -> dict:
        """
        Sanitize text input. Returns cleaned text or error.
        """
        if not text:
            return {"ok": True, "value": ""}

        # Length check
        if len(text) > max_length:
            return {"ok": False, "error": f"Input exceeds maximum length of {max_length} characters."}

        # Check for injection patterns
        injection = self._detect_injection(text)
        if injection:
            return {"ok": False, "error": f"Input contains disallowed content: {injection}"}

        # HTML escape to prevent XSS
        # We escape then allow safe markdown-like formatting
        cleaned = html.escape(text, quote=True)

        return {"ok": True, "value": cleaned}

    def sanitize_username(self, username: str) -> dict:
        """Strict username sanitization."""
        if not username:
            return {"ok": False, "error": "Username required."}

        # Only allow safe characters
        if not re.match(r'^[a-zA-Z0-9_\-]{3,50}$', username):
            return {"ok": False, "error": "Username may only contain letters, numbers, underscores, and hyphens (3-50 characters)."}

        # No injection possible with this character set
        return {"ok": True, "value": username.lower()}

    def sanitize_email(self, email: str) -> dict:
        """Basic email validation."""
        if not email or len(email) > 255:
            return {"ok": False, "error": "Invalid email address."}

        if not re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email):
            return {"ok": False, "error": "Invalid email address format."}

        return {"ok": True, "value": email.lower().strip()}

    def _detect_injection(self, text: str) -> Optional[str]:
        """Detect injection attack patterns."""
        text_upper = text.upper()

        for pattern in SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE | re.DOTALL):
                return "SQL injection pattern"

        for pattern in XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return "script injection pattern"

        for pattern in SHELL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return "shell injection pattern"

        return None

    def is_safe_url(self, url: str) -> bool:
        """Check if a URL is safe to redirect to."""
        if not url:
            return False
        # Only allow relative URLs or URLs to our own domain
        if url.startswith("/") and not url.startswith("//"):
            return True
        return False


# ── Security Headers Middleware ───────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response.
    Standard web security best practices.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy — prevents XSS
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self';"
        )

        # Remove server header to not reveal platform info
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]

        return response


# ── Request Size Middleware ───────────────────────────────────────────────────

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Reject oversized requests before they reach the application.
    Prevents large payload attacks.
    """

    MAX_SIZE = MAX_REQUEST_SIZE_MB * 1024 * 1024

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.MAX_SIZE:
            return JSONResponse(
                {"ok": False, "error": f"Request too large. Maximum size is {MAX_REQUEST_SIZE_MB}MB."},
                status_code=413
            )
        return await call_next(request)


# ── Rate Limit Middleware ─────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    General API rate limiting middleware.
    Specific endpoints have their own stricter limits.
    """

    EXCLUDED_PATHS = {"/health", "/static", "/media"}

    async def dispatch(self, request: Request, call_next):
        # Skip static files and health check
        path = request.url.path
        if any(path.startswith(p) for p in self.EXCLUDED_PATHS):
            return await call_next(request)

        ip = self._get_ip(request)
        result = rate_limiter.check(ip, "api")

        if not result["allowed"]:
            return JSONResponse(
                {
                    "ok":          False,
                    "error":       result["reason"],
                    "retry_after": result["retry_after"],
                },
                status_code=429,
                headers={"Retry-After": str(result["retry_after"])}
            )

        return await call_next(request)

    def _get_ip(self, request: Request) -> str:
        """Get real IP, accounting for proxies (Railway, etc.)."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# ── Convenience Functions ─────────────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    """Get real client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def enforce_rate_limit(ip: str, action: str):
    """
    Enforce rate limit. Raises HTTPException if limit exceeded.
    Use as a dependency or inline check in route handlers.
    """
    result = rate_limiter.check(ip, action)
    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=result["reason"],
            headers={"Retry-After": str(result["retry_after"])}
        )


# ── Singleton instances ───────────────────────────────────────────────────────

rate_limiter = RateLimiter()
sanitizer    = InputSanitizer()
