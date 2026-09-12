"""
patch_profile_edit_youtube.py

Adds a YouTube input field + save/prefill logic to templates/profile_edit.html,
matching the existing Twitch/Spotify pattern.

Run once from your project root:
    python3 patch_profile_edit_youtube.py
"""

PATH = "templates/profile_edit.html"

FORM_ANCHOR = """    <label>Spotify <small>(track, artist, album, or playlist link — leave blank to remove)</small>
      <input type="text" id="spotify" placeholder="Paste a Spotify share link">
    </label>"""

FORM_NEW = """    <label>Spotify <small>(track, artist, album, or playlist link — leave blank to remove)</small>
      <input type="text" id="spotify" placeholder="Paste a Spotify share link">
    </label>

    <label>YouTube <small>(video or channel link — leave blank to remove)</small>
      <input type="text" id="youtube" placeholder="Paste a video or channel link">
    </label>"""

LOAD_ANCHOR = """      document.getElementById('spotify').value = p.connections.spotify_url ? p.connections.spotify_url : '';"""

LOAD_NEW = """      document.getElementById('spotify').value = p.connections.spotify_url ? p.connections.spotify_url : '';
      document.getElementById('youtube').value = p.connections.youtube_video_url ? p.connections.youtube_video_url : (p.connections.youtube_channel_url ? p.connections.youtube_channel_url : '');"""

SAVE_VAR_ANCHOR = """  const spotify = document.getElementById('spotify').value.trim();"""

SAVE_VAR_NEW = """  const spotify = document.getElementById('spotify').value.trim();
  const youtube = document.getElementById('youtube').value.trim();"""

SAVE_CALL_ANCHOR = """    f.append('spotify', spotify);
    const r = await fetch('/api/profile/spotify', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }"""

SAVE_CALL_NEW = """    f.append('spotify', spotify);
    const r = await fetch('/api/profile/spotify', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }

  if (ok) {
    const f = new FormData();
    f.append('youtube', youtube);
    const r = await fetch('/api/profile/youtube', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }"""


def apply_patch(content, anchor, new, label):
    count = content.count(anchor)
    if count == 0:
        print(f"ERROR: anchor for '{label}' not found. Aborting before any write.")
        return None
    if count > 1:
        print(f"ERROR: anchor for '{label}' matched {count} times (expected 1). Aborting — needs manual review.")
        return None
    return content.replace(anchor, new, 1)


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'id="youtube"' in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, FORM_ANCHOR, FORM_NEW, "form field")
    if content2 is None:
        return

    content3 = apply_patch(content2, LOAD_ANCHOR, LOAD_NEW, "prefill on load")
    if content3 is None:
        return

    content4 = apply_patch(content3, SAVE_VAR_ANCHOR, SAVE_VAR_NEW, "save variable")
    if content4 is None:
        return

    content5 = apply_patch(content4, SAVE_CALL_ANCHOR, SAVE_CALL_NEW, "save API call")
    if content5 is None:
        return

    with open(PATH, "w") as f:
        f.write(content5)

    print("Patched templates/profile_edit.html successfully.")


if __name__ == "__main__":
    main()
