"""
patch_compact_connection_icons.py

Replaces the full-width "View on X" buttons for link-only connections
(YouTube channel, Bluesky, TikTok) with a compact row of small icon
links. Embedded players (Twitch, Spotify, YouTube video) stay as full
embeds.

Run once from your project root:
    python3 patch_compact_connection_icons.py
"""

PATH = "templates/profile.html"

ANCHOR = '''      } else if (c.youtube_channel_url) {
        html += '<a href="' + c.youtube_channel_url + '" target="_blank" rel="noopener noreferrer" class="vote-btn" style="text-align:center;text-decoration:none;display:block;">\\u25b6 View YouTube Channel</a>';
      }
      if (c.bluesky_url) {
        html += '<a href="' + c.bluesky_url + '" target="_blank" rel="noopener noreferrer" class="vote-btn" style="text-align:center;text-decoration:none;display:block;">View on Bluesky</a>';
      }
      if (c.tiktok_url) {
        html += '<a href="' + c.tiktok_url + '" target="_blank" rel="noopener noreferrer" class="vote-btn" style="text-align:center;text-decoration:none;display:block;">View on TikTok</a>';
      }'''

NEW = '''      }

      const iconLinks = [];
      if (c.youtube_channel_url && !c.youtube_video_url) {
        iconLinks.push({ url: c.youtube_channel_url, icon: '\\u25b6', label: 'YouTube' });
      }
      if (c.bluesky_url) {
        iconLinks.push({ url: c.bluesky_url, icon: '\\ud83e\\udd8b', label: 'Bluesky' });
      }
      if (c.tiktok_url) {
        iconLinks.push({ url: c.tiktok_url, icon: '\\u266a', label: 'TikTok' });
      }
      if (iconLinks.length) {
        html += '<div style="display:flex;gap:10px;flex-wrap:wrap;">';
        iconLinks.forEach(function(l) {
          html += '<a href="' + l.url + '" target="_blank" rel="noopener noreferrer" title="' + l.label + '" style="display:flex;align-items:center;gap:5px;padding:6px 12px;border-radius:16px;background:var(--green-mid, #eef3ee);color:var(--green-dark, #2e7d52);text-decoration:none;font-size:13px;font-weight:600;">' + l.icon + ' ' + l.label + '</a>';
        });
        html += '</div>';
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

    if "iconLinks" in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, ANCHOR, NEW, "compact connection icons")
    if content2 is None:
        return

    with open(PATH, "w") as f:
        f.write(content2)

    print("Patched templates/profile.html successfully.")


if __name__ == "__main__":
    main()
