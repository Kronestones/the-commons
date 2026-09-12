"""
patch_profile_connections_display.py

Adds the Twitch/Spotify/YouTube connections display block to
templates/profile.html, right after the bio is rendered. Combines
what should have been two earlier patches into one, since the first
never actually made it into this file.

Run once from your project root:
    python3 patch_profile_connections_display.py
"""

PATH = "templates/profile.html"

ANCHOR = """    if (p.bio) {
      const bioEl = document.getElementById('profile-bio');
      bioEl.textContent = p.bio;
      bioEl.style.display = '';
    }"""

NEW_BLOCK = """
    if (p.connections && (p.connections.twitch_url || p.connections.spotify_url || p.connections.youtube_video_url || p.connections.youtube_channel_url)) {
      const c = p.connections;
      let html = '<div class="profile-connections" style="margin-top:16px;display:flex;flex-direction:column;gap:12px;">';
      if (c.twitch_url) {
        html += '<iframe src="' + c.twitch_url + '" height="280" width="100%" allowfullscreen frameborder="0" scrolling="no"></iframe>';
      }
      if (c.spotify_url) {
        html += '<iframe src="' + c.spotify_url + '" width="100%" height="152" frameborder="0" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture" style="border-radius:12px;"></iframe>';
      }
      if (c.youtube_video_url) {
        html += '<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;"><iframe src="' + c.youtube_video_url + '" style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen frameborder="0"></iframe></div>';
      } else if (c.youtube_channel_url) {
        html += '<a href="' + c.youtube_channel_url + '" target="_blank" rel="noopener noreferrer" class="vote-btn" style="text-align:center;text-decoration:none;display:block;">\\u25b6 View YouTube Channel</a>';
      }
      html += '</div>';
      const existing = document.getElementById('profile-connections-wrap');
      if (existing) existing.remove();
      const wrap = document.createElement('div');
      wrap.id = 'profile-connections-wrap';
      wrap.innerHTML = html;
      document.getElementById('profile-info').appendChild(wrap);
    }"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "profile-connections-wrap" in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting — needs manual review.")
        return

    content = content.replace(ANCHOR, ANCHOR + NEW_BLOCK, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched templates/profile.html successfully.")


if __name__ == "__main__":
    main()
