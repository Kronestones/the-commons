"""
create_news_outlets.py — one-time setup script

Creates a User account for each outlet in commons/news_feed.py's
NEWS_OUTLETS list, so the news poller has an account to post as.

These accounts work like a news outlet's bot account on X or
Substack — they post their latest headlines automatically, people
can follow/like/comment/share those posts same as any other, but
nobody logs in as these accounts day-to-day.

Safe to re-run — skips any outlet that already has an account.

Run once from your project root:
    python3 create_news_outlets.py
"""

import secrets
from commons.database import SessionLocal, User
from commons.news_feed import NEWS_OUTLETS

# Outlet display names — shown on their posts/profile.
DISPLAY_NAMES = {
    "BBCNews":     "BBC News",
    "NPR":         "NPR",
    "AlJazeera":   "Al Jazeera",
    "CBCNews":     "CBC News",
    "MotherJones": "Mother Jones",
    "MsMagazine":  "Ms. Magazine",
    "AmnestyIntl": "Amnesty International",
}


def main():
    db = SessionLocal()
    created = []
    skipped = []

    try:
        for outlet in NEWS_OUTLETS:
            username = outlet["username"]
            display_name = DISPLAY_NAMES.get(username, username)

            existing = db.query(User).filter(User.username.ilike(username)).first()
            if existing:
                skipped.append(username)
                continue

            placeholder_email = f"outlet-{username.lower()}@news.thecommons.internal"

            # These accounts never log in via password — no human ever
            # authenticates as a news outlet — so we skip bcrypt entirely
            # here rather than depend on a native compiler being available
            # wherever this script runs. The stored value is unusable as
            # a real password hash, which is exactly the point.
            unusable_hash = "outlet_account_no_login:" + secrets.token_urlsafe(32)

            user = User(
                username      = username,
                email         = placeholder_email,
                password_hash = unusable_hash,
                display_name  = display_name,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            created.append(username)
            print(f"Created: @{username} ({display_name})")

        print()
        print(f"Done. Created {len(created)}, skipped {len(skipped)} (already existed).")
        if skipped:
            print(f"Already existed: {', '.join(skipped)}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
