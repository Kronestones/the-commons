"""
patch_youtube_connection.py

Adds YouTube support to commons/connections.py:
- parse_youtube_input(): accepts a video URL (any common format) or a
  channel URL, returns {"type": "video", "id": VIDEO_ID} or
  {"type": "channel", "url": CHANNEL_URL}
- youtube_embed_url(): builds the video embed URL (channels have no
  embeddable player — just returned as a link)
- set_youtube_connection() / removal via remove_connection("youtube")
- get_profile_embeds() extended with youtube_video_url / youtube_channel_url

Run once from your project root:
    python3 patch_youtube_connection.py
"""

PATH = "commons/connections.py"

# ── 1. Parsing + embed builder (inserted after spotify_embed_url) ───────
INSERT_AFTER_ANCHOR = """def spotify_embed_url(spotify_type: str, spotify_id: str) -> str:
    return f"https://open.spotify.com/embed/{spotify_type}/{spotify_id}\""""

INSERT_NEW = """def spotify_embed_url(spotify_type: str, spotify_id: str) -> str:
    return f"https://open.spotify.com/embed/{spotify_type}/{spotify_id}"


# YouTube video IDs are 11 characters, base64url-ish charset.
_YOUTUBE_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def parse_youtube_input(raw: str) -> Optional[dict]:
    \"\"\"
    Accepts a YouTube video URL (watch, youtu.be, shorts, embed) or a
    channel URL (/channel/, /c/, /@handle). Returns:
      {"type": "video", "id": VIDEO_ID}
      {"type": "channel", "url": full channel URL}
    or None if it doesn't look like YouTube at all.
    \"\"\"
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
    return f"https://www.youtube.com/embed/{video_id}\""""


# ── 2. remove_connection extension ───────────────────────────────────────
REMOVE_ANCHOR = """    elif kind == "spotify":
        data.pop("spotify_type", None)
        data.pop("spotify_id", None)
    else:"""

REMOVE_NEW = """    elif kind == "spotify":
        data.pop("spotify_type", None)
        data.pop("spotify_id", None)
    elif kind == "youtube":
        data.pop("youtube_type", None)
        data.pop("youtube_id", None)
        data.pop("youtube_channel_url", None)
    else:"""

# ── 3. set_youtube_connection (inserted after set_spotify_connection) ───
SET_ANCHOR_MARKER = "def remove_connection(user, kind: str) -> dict:"

SET_YOUTUBE_FN = '''def set_youtube_connection(user, raw_input: str) -> dict:
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


'''

# ── 4. get_profile_embeds extension ──────────────────────────────────────
EMBEDS_ANCHOR = '''    result = {"twitch_url": None, "spotify_url": None}

    if data.get("twitch_channel"):
        result["twitch_url"] = twitch_embed_url(data["twitch_channel"], parent_domain)

    if data.get("spotify_type") and data.get("spotify_id"):
        result["spotify_url"] = spotify_embed_url(data["spotify_type"], data["spotify_id"])

    return result'''

EMBEDS_NEW = '''    result = {
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

    return result'''

# ── 5. import fix: need `re` module ──────────────────────────────────────
IMPORT_ANCHOR = "import json\nimport re"


def apply_patch(content, anchor, new, label, allow_missing_ok=False):
    count = content.count(anchor)
    if count == 0:
        if allow_missing_ok:
            return content
        print(f"ERROR: anchor for '{label}' not found. Aborting before any write.")
        return None
    if count > 1:
        print(f"ERROR: anchor for '{label}' matched {count} times (expected 1). Aborting — needs manual review.")
        return None
    return content.replace(anchor, new, 1)


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "def parse_youtube_input" in content:
        print("Already patched — no changes made.")
        return

    if IMPORT_ANCHOR not in content:
        print("ERROR: expected 'import json\\nimport re' at top of file — check imports manually, `re` module is required.")
        return

    content2 = apply_patch(content, INSERT_AFTER_ANCHOR, INSERT_NEW, "youtube parsing + embed builder")
    if content2 is None:
        return

    content3 = apply_patch(content2, REMOVE_ANCHOR, REMOVE_NEW, "remove_connection youtube support")
    if content3 is None:
        return

    if SET_ANCHOR_MARKER not in content3:
        print("ERROR: could not find remove_connection() to insert set_youtube_connection before it.")
        return
    content4 = content3.replace(SET_ANCHOR_MARKER, SET_YOUTUBE_FN + SET_ANCHOR_MARKER, 1)

    content5 = apply_patch(content4, EMBEDS_ANCHOR, EMBEDS_NEW, "get_profile_embeds youtube fields")
    if content5 is None:
        return

    with open(PATH, "w") as f:
        f.write(content5)

    print("Patched commons/connections.py successfully.")


if __name__ == "__main__":
    main()
