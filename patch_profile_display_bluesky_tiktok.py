"""
patch_profile_display_bluesky_tiktok.py

Adds Bluesky and TikTok display to templates/profile.html, right
alongside the existing Twitch/Spotify/YouTube connections block.
Both render as simple profile links (per the user's decision — no
embed widget for either), matching the YouTube-channel-link pattern.

Run once from your project root:
    python3 patch_profile_display_bluesky_tiktok.py
"""

PATH = "templates/profile.html"

CONDITION_ANCHOR = '''    if (p.connections && (p.connections.twitch_url || p.connections.spotify_url || p.connections.youtube_video_url || p.connections.youtube_channel_url)) {'''

CONDITION_NEW = '''    if (p.connections && (p.connections.twitch_url || p.connections.spotify_url || p.connections.youtube_video_url || p.connections.youtube_channel_url || p.connections.bluesky_url || p.connections.tiktok_url)) {'''

YOUTUBE_BLOCK_ANCHOR = '''      } else if (c.youtube_channel_url) {
        html += '<a href="' + c.youtube_channel_url + '" target="_blank" rel="noopener noreferrer" class="vote-btn" style="text-align:center;text-decoration:none;display:block;">\\u25b6 View YouTube Channel</a>';
      }'''

YOUTUBE_BLOCK_NEW = '''      } else if (c.youtube_channel_url) {
        html += '<a href="' + c.youtube_channel_url + '" target="_blank" rel="noopener noreferrer" class="vote-btn" style="text-align:center;text-decoration:none;display:block;">\\u25b6 View YouTube Channel</a>';
      }
      if (c.bluesky_url) {
        html += '<a href="' + c.bluesky_url + '" target="_blank" rel="noopener noreferrer" class="vote-btn" style="text-align:center;text-decoration:none;display:block;">View on Bluesky</a>';
      }
      if (c.tiktok_url) {
        html += '<a href="' + c.tiktok_url + '" target="_blank" rel="noopener noreferrer" class="vote-btn" style="text-align:center;text-decoration:none;display:block;">View on TikTok</a>';
      }'''


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

    if "bluesky_url" in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, CONDITION_ANCHOR, CONDITION_NEW, "connections visibility condition")
    if content2 is None:
        return

    content3 = apply_patch(content2, YOUTUBE_BLOCK_ANCHOR, YOUTUBE_BLOCK_NEW, "bluesky/tiktok display block")
    if content3 is None:
        return

    with open(PATH, "w") as f:
        f.write(content3)

    print("Patched templates/profile.html successfully.")


if __name__ == "__main__":
    main()
