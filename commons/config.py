"""
config.py — The Commons Configuration

Reads environment. Validates settings. Reports status.
"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:

    def __init__(self):
        self.secret_key       = os.getenv("SECRET_KEY", secrets.token_hex(32))
        self.environment      = os.getenv("ENVIRONMENT", "development")
        self.debug            = os.getenv("DEBUG", "true").lower() == "true"
        self.host             = os.getenv("HOST", "0.0.0.0")
        self.port             = int(os.getenv("PORT", 8000))
        self.base_url = os.getenv("BASE_URL", "https://the-commons.onrender.com")
        self.database_url     = os.getenv("DATABASE_URL", "sqlite:///./the_commons.db")
        self.media_dir        = Path(os.getenv("MEDIA_DIR", "./media"))
        self.max_upload_mb    = int(os.getenv("MAX_UPLOAD_MB", 100))
        self.sovereign_hash   = os.getenv("SOVEREIGN_KEY_HASH", "")
        self.sovereign_salt   = os.getenv("SOVEREIGN_SALT", "")
        self.fingerprint_on   = os.getenv("FINGERPRINT_ENABLED", "true").lower() == "true"
        self.transaction_fee  = float(os.getenv("TRANSACTION_FEE", 1.00))
        self.min_circle_size  = int(os.getenv("MIN_CIRCLE_SIZE", 3))

        # JWT
        self.jwt_algorithm    = "HS256"
        self.jwt_expire_hours = 24 * 7   # 7 days

        # Ensure media directory exists
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def is_ready(self) -> bool:
        problems = self.validate()
        return len(problems) == 0

    def validate(self) -> list:
        problems = []
        if self.secret_key == "change-this-to-a-long-random-string":
            problems.append("SECRET_KEY is not set — using insecure default")
        if not self.media_dir.exists():
            problems.append(f"Media directory does not exist: {self.media_dir}")
        if self.transaction_fee != 1.00:
            problems.append(f"Transaction fee is not $1.00 — check configuration")
        return problems

    def print_status(self):
        print(f"\n[CONFIG] The Commons Configuration")
        print(f"[CONFIG]   Environment : {self.environment}")
        print(f"[CONFIG]   Host        : {self.host}:{self.port}")
        print(f"[CONFIG]   Database    : {self.database_url}")
        print(f"[CONFIG]   Media dir   : {self.media_dir}")
        print(f"[CONFIG]   Fingerprint : {'ON' if self.fingerprint_on else 'OFF'}")
        print(f"[CONFIG]   Fee         : ${self.transaction_fee:.2f}")
        problems = self.validate()
        if problems:
            print(f"[CONFIG]   Warnings:")
            for p in problems:
                print(f"[CONFIG]     · {p}")
        else:
            print(f"[CONFIG]   Status      : READY")

config = Config()
