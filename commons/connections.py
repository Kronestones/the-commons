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


def remove_connection(user, kind: str) -> dict:
    """kind is 'twitch' or 'spotify'."""
    data = load_connections(user)
    if kind == "twitch":
        data.pop("twitch_channel", None)
    elif kind == "spotify":
        data.pop("spotify_type", None)
        data.pop("spotify_id", None)
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
    result = {"twitch_url": None, "spotify_url": None}

    if data.get("twitch_channel"):
        result["twitch_url"] = twitch_embed_url(data["twitch_channel"], parent_domain)

    if data.get("spotify_type") and data.get("spotify_id"):
        result["spotify_url"] = spotify_embed_url(data["spotify_type"], data["spotify_id"])

    return result
