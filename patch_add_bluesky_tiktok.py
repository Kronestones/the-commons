"""
patch_add_bluesky_tiktok.py

Adds Bluesky and TikTok as simple profile-link connections (no embed
widget/script for either — user decided both should just be a plain
link to their profile).

Run once from your project root:
    python3 patch_add_bluesky_tiktok.py
"""

PATH = "commons/connections.py"

INSERT_AFTER_ANCHOR = '''def youtube_video_embed_url(video_id: str) -> str:
    return f"https://www.youtube.com/embed/{video_id}"'''

INSERT_NEW = '''def youtube_video_embed_url(video_id: str) -> str:
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
    return f"https://www.tiktok.com/@{username}"'''

SET_ANCHOR_MARKER = "def remove_connection(user, kind: str) -> dict:"

SET_FUNCTIONS = '''def set_bluesky_connection(user, raw_input: str) -> dict:
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


'''

REMOVE_ANCHOR = '''    elif kind == "youtube":
        data.pop("youtube_type", None)
        data.pop("youtube_id", None)
        data.pop("youtube_channel_url", None)
    else:'''

REMOVE_NEW = '''    elif kind == "youtube":
        data.pop("youtube_type", None)
        data.pop("youtube_id", None)
        data.pop("youtube_channel_url", None)
    elif kind == "bluesky":
        data.pop("bluesky_handle", None)
    elif kind == "tiktok":
        data.pop("tiktok_username", None)
    else:'''

EMBEDS_ANCHOR = '''    if data.get("youtube_type") == "video" and data.get("youtube_id"):
        result["youtube_video_url"] = youtube_video_embed_url(data["youtube_id"])
    elif data.get("youtube_type") == "channel" and data.get("youtube_channel_url"):
        result["youtube_channel_url"] = data["youtube_channel_url"]

    return result'''

EMBEDS_NEW = '''    if data.get("youtube_type") == "video" and data.get("youtube_id"):
        result["youtube_video_url"] = youtube_video_embed_url(data["youtube_id"])
    elif data.get("youtube_type") == "channel" and data.get("youtube_channel_url"):
        result["youtube_channel_url"] = data["youtube_channel_url"]

    if data.get("bluesky_handle"):
        result["bluesky_url"] = bluesky_profile_url(data["bluesky_handle"])

    if data.get("tiktok_username"):
        result["tiktok_url"] = tiktok_profile_url(data["tiktok_username"])

    return result'''


def apply_patch(content, anchor, new, label):
    count = content.count(anchor)
    if count == 0:
        print(f"ERROR: anchor for '{label}' not found. Aborting before any write.")
        return None
    if count > 1:
        print(f"ERROR: anchor for '{label}' matched {count} times (expected 1). Aborting.")
        return None
    return content.replace(anchor, new, 1)


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "def parse_bluesky_input" in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, INSERT_AFTER_ANCHOR, INSERT_NEW, "bluesky/tiktok parsing")
    if content2 is None:
        return

    if SET_ANCHOR_MARKER not in content2:
        print("ERROR: could not find remove_connection() to insert set functions before it.")
        return
    content3 = content2.replace(SET_ANCHOR_MARKER, SET_FUNCTIONS + SET_ANCHOR_MARKER, 1)

    content4 = apply_patch(content3, REMOVE_ANCHOR, REMOVE_NEW, "remove_connection bluesky/tiktok support")
    if content4 is None:
        return

    content5 = apply_patch(content4, EMBEDS_ANCHOR, EMBEDS_NEW, "get_profile_embeds bluesky/tiktok fields")
    if content5 is None:
        return

    with open(PATH, "w") as f:
        f.write(content5)

    print("Patched commons/connections.py successfully.")


if __name__ == "__main__":
    main()
