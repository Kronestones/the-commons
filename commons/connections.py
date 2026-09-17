"""
connections.py — The Commons Profile Connections (Twitch, Spotify)

Lets a user paste a Twitch channel link and/or a Spotify link (track,
album, artist, or playlist) into their profile. We parse whatever they
paste into the pieces needed to build a safe embed iframe, and store
those pieces (not raw HTML) on the User row.

No API keys required. No cost. Twitch and Spotify host all the media —
this only ever produces an iframe URL.

Storage: one Text column on User, `connections`, holding a JSON blob:
    {
      "twitch_channel": "somechannel",
      "spotify_type": "track",
      "spotify_id": "07WEDHF2YwVgYuBugi2ECO"
    }
Any key can be absent if the user hasn't set that connection.

Add to commons/database.py, inside class User(Base):
    connections = Column(Text, default="{}")

Nothing else in the schema changes. No new table, no migration beyond
the one new column.
"""

import json
import re
from typing import Optional
from urllib.parse import urlparse, parse_qs

# ── Parsing ──────────────────────────────────────────────────────────────

# Twitch channel names: 4-25 chars, alphanumeric + underscore, can't start
# with a number per Twitch's own username rules — but we don't need to be
# strict here, just safe. Reject anything that isn't this shape.
_TWITCH_NAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,25}$")

# Spotify IDs are base62, always 22 characters, in practice. We validate
# shape, not existence — actual existence can only be confirmed by the
# embed loading client-side, which this module doesn't control.
_SPOTIFY_ID_RE = re.compile(r"^[a-zA-Z0-9]{22}$")
_SPOTIFY_TYPES = {"track", "album", "artist", "playlist", "episode", "show"}


def parse_twitch_input(raw: str) -> Optional[str]:
    """
    Accepts either a bare channel name ("somechannel") or a full URL
    (https://www.twitch.tv/somechannel) and returns just the channel
    name, or None if it doesn't look like a valid Twitch channel.
    """
    raw = raw.strip()
    if not raw:
        return None

    if "twitch.tv" in raw:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        # path looks like "/somechannel" or "/somechannel/videos" etc —
        # we only want the first segment.
        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            return None
        channel = parts[0]
    else:
        channel = raw

    channel = channel.lower()
    if not _TWITCH_NAME_RE.match(channel):
        return None
    return channel


def parse_spotify_input(raw: str) -> Optional[dict]:
    """
    Accepts a Spotify share link, e.g.:
      https://open.spotify.com/track/07WEDHF2YwVgYuBugi2ECO?si=...
      https://open.spotify.com/playlist/37i9dQZEVXbMZ5PAcNTDXd
    Returns {"type": "track", "id": "07WEDHF2YwVgYuBugi2ECO"} or None.
    """
    raw = raw.strip()
    if not raw:
        return None

    if "open.spotify.com" not in raw:
        return None

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    parts = [p for p in parsed.path.split("/") if p]

    # Path shape is /{type}/{id} — sometimes prefixed with a locale like
    # /intl-en/track/{id}, so check the last two segments specifically.
    if len(parts) < 2:
        return None

    spotify_type, spotify_id = parts[-2], parts[-1]
    # Strip anything after a colon or query artifact that slipped through
    spotify_id = spotify_id.split("?")[0]

    if spotify_type not in _SPOTIFY_TYPES:
        return None
    if not _SPOTIFY_ID_RE.match(spotify_id):
        return None

    return {"type": spotify_type, "id": spotify_id}


# ── Embed URL builders ──────────────────────────────────────────────────

def twitch_embed_url(channel: str, parent_domain: str) -> str:
    """
    parent_domain must be the exact domain the page is served from,
    e.g. "commonscommunity.org" — Twitch rejects embeds without a
    matching parent param.
    """
    return f"https://player.twitch.tv/?channel={channel}&parent={parent_domain}"


def spotify_embed_url(spotify_type: str, spotify_id: str) -> str:
    return f"https://open.spotify.com/embed/{spotify_type}/{spotify_id}"


# YouTube video IDs are 11 characters, base64url-ish charset.
_YOUTUBE_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def parse_youtube_input(raw: str) -> Optional[dict]:
    """
    Accepts a YouTube video URL (watch, youtu.be, shorts, embed) or a
    channel URL (/channel/, /c/, /@handle). Returns:
      {"type": "video", "id": VIDEO_ID}
      {"type": "channel", "url": full channel URL}
    or None if it doesn't look like YouTube at all.
    """
    raw = raw.strip()
    if not raw:
        return None

    if "youtube.com" not in raw and "youtu.be" not in raw:
        return None

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")

    # youtu.be/VIDEO_ID short links
    if "youtu.be" in parsed.netloc:
        video_id = parsed.path.strip("/").split("/")[0]
        if _YOUTUBE_VIDEO_ID_RE.match(video_id):
            return {"type": "video", "id": video_id}
        return None

    # youtube.com/watch?v=VIDEO_ID
    if parsed.path == "/watch":
        qs = parse_qs(parsed.query)
        video_id = qs.get("v", [None])[0]
        if video_id and _YOUTUBE_VIDEO_ID_RE.match(video_id):
            return {"type": "video", "id": video_id}
        return None

    parts = [p for p in parsed.path.split("/") if p]
    if not parts:
        return None

    # youtube.com/embed/VIDEO_ID or /shorts/VIDEO_ID
    if parts[0] in ("embed", "shorts") and len(parts) >= 2:
        video_id = parts[1]
        if _YOUTUBE_VIDEO_ID_RE.match(video_id):
            return {"type": "video", "id": video_id}
        return None

    # youtube.com/channel/UC..., /c/Name, /@handle
    if parts[0] in ("channel", "c") or parts[0].startswith("@"):
        return {"type": "channel", "url": f"https://www.youtube.com/{'/'.join(parts)}"}

    return None


def youtube_video_embed_url(video_id: str) -> str:
    return f"https://www.youtube.com/embed/{video_id}"


_BLUESKY_HANDLE_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9.-]{1,251}[a-zA-Z0-9]$")
_TIKTOK_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.]{2,24}$")


def parse_bluesky_input(raw: str) -> Optional[str]:
    raw = raw.strip()
    if not raw:
        return None

    if "bsky.app" in raw:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2 and parts[0] == "profile":
            handle = parts[1]
        else:
            return None
    else:
        handle = raw.lstrip("@")

    if not _BLUESKY_HANDLE_RE.match(handle):
        return None
    return handle


def bluesky_profile_url(handle: str) -> str:
    return f"https://bsky.app/profile/{handle}"


def parse_tiktok_input(raw: str) -> Optional[str]:
    raw = raw.strip()
    if not raw:
        return None

    if "tiktok.com" in raw:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        parts = [p for p in parsed.path.split("/") if p]
        if not parts:
            return None
        username = parts[0].lstrip("@")
    else:
        username = raw.lstrip("@")

    if not _TIKTOK_USERNAME_RE.match(username):
        return None
    return username


def tiktok_profile_url(username: str) -> str:
    return f"https://www.tiktok.com/@{username}"


# ── Read/write helpers for the User.connections JSON column ─────────────

def load_connections(user) -> dict:
    """Safely parse a User's connections column. Never raises."""
    if not user.connections:
        return {}
    try:
        return json.loads(user.connections)
    except (json.JSONDecodeError, TypeError):
        return {}


def set_twitch_connection(user, raw_input: str) -> dict:
    """
    Validates and stores a Twitch connection on the user object
    (caller is responsible for db.commit()).
    Returns {"ok": True} or {"ok": False, "error": "..."}.
    """
    channel = parse_twitch_input(raw_input)
    if not channel:
        return {"ok": False, "error": "That doesn't look like a valid Twitch channel or link."}

    data = load_connections(user)
    data["twitch_channel"] = channel
    user.connections = json.dumps(data)
    return {"ok": True, "channel": channel}


def set_spotify_connection(user, raw_input: str) -> dict:
    """
    Validates and stores a Spotify connection on the user object
    (caller is responsible for db.commit()).
    """
    parsed = parse_spotify_input(raw_input)
    if not parsed:
        return {"ok": False, "error": "That doesn't look like a valid Spotify link."}

    data = load_connections(user)
    data["spotify_type"] = parsed["type"]
    data["spotify_id"] = parsed["id"]
    user.connections = json.dumps(data)
    return {"ok": True, **parsed}


def set_youtube_connection(user, raw_input: str) -> dict:
    """
    Validates and stores a YouTube connection (video or channel) on the
    user object (caller is responsible for db.commit()).
    """
    parsed = parse_youtube_input(raw_input)
    if not parsed:
        return {"ok": False, "error": "That doesn't look like a valid YouTube link."}

    data = load_connections(user)
    if parsed["type"] == "video":
        data["youtube_type"] = "video"
        data["youtube_id"] = parsed["id"]
        data.pop("youtube_channel_url", None)
    else:
        data["youtube_type"] = "channel"
        data["youtube_channel_url"] = parsed["url"]
        data.pop("youtube_id", None)
    user.connections = json.dumps(data)
    return {"ok": True, **parsed}


def set_bluesky_connection(user, raw_input: str) -> dict:
    handle = parse_bluesky_input(raw_input)
    if not handle:
        return {"ok": False, "error": "That doesn't look like a valid Bluesky handle or link."}

    data = load_connections(user)
    data["bluesky_handle"] = handle
    user.connections = json.dumps(data)
    return {"ok": True, "handle": handle}


def set_tiktok_connection(user, raw_input: str) -> dict:
    username = parse_tiktok_input(raw_input)
    if not username:
        return {"ok": False, "error": "That doesn't look like a valid TikTok username or link."}

    data = load_connections(user)
    data["tiktok_username"] = username
    user.connections = json.dumps(data)
    return {"ok": True, "username": username}


def remove_connection(user, kind: str) -> dict:
    """kind is 'twitch' or 'spotify'."""
    data = load_connections(user)
    if kind == "twitch":
        data.pop("twitch_channel", None)
    elif kind == "spotify":
        data.pop("spotify_type", None)
        data.pop("spotify_id", None)
    elif kind == "youtube":
        data.pop("youtube_type", None)
        data.pop("youtube_id", None)
        data.pop("youtube_channel_url", None)
    elif kind == "bluesky":
        data.pop("bluesky_handle", None)
    elif kind == "tiktok":
        data.pop("tiktok_username", None)
    else:
        return {"ok": False, "error": f"Unknown connection kind: {kind}"}
    user.connections = json.dumps(data)
    return {"ok": True}


def get_profile_embeds(user, parent_domain: str) -> dict:
    """
    Returns the embed URLs ready to drop into a template, or None
    for whichever connection isn't set. Use in the profile route:
        embeds = get_profile_embeds(user, "commonscommunity.org")
    """
    data = load_connections(user)
    result = {
        "twitch_url": None,
        "spotify_url": None,
        "youtube_video_url": None,
        "youtube_channel_url": None,
    }

    if data.get("twitch_channel"):
        result["twitch_url"] = twitch_embed_url(data["twitch_channel"], parent_domain)

    if data.get("spotify_type") and data.get("spotify_id"):
        result["spotify_url"] = spotify_embed_url(data["spotify_type"], data["spotify_id"])

    if data.get("youtube_type") == "video" and data.get("youtube_id"):
        result["youtube_video_url"] = youtube_video_embed_url(data["youtube_id"])
    elif data.get("youtube_type") == "channel" and data.get("youtube_channel_url"):
        result["youtube_channel_url"] = data["youtube_channel_url"]

    if data.get("bluesky_handle"):
        result["bluesky_url"] = bluesky_profile_url(data["bluesky_handle"])

    if data.get("tiktok_username"):
        result["tiktok_url"] = tiktok_profile_url(data["tiktok_username"])

    return result
