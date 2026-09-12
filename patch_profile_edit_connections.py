"""
patch_profile_edit_connections.py

Adds Twitch and Spotify input fields + save logic to templates/profile_edit.html.

Run once from your project root:
    python3 patch_profile_edit_connections.py
"""

PATH = "templates/profile_edit.html"

FORM_ANCHOR = """    <div id="edit-msg" class="form-error" style="display:none;"></div>"""

FORM_NEW = """    <label>Twitch <small>(channel name or link — leave blank to remove)</small>
      <input type="text" id="twitch" placeholder="e.g. yourchannel or https://twitch.tv/yourchannel">
    </label>

    <label>Spotify <small>(track, artist, album, or playlist link — leave blank to remove)</small>
      <input type="text" id="spotify" placeholder="Paste a Spotify share link">
    </label>

    <div id="edit-msg" class="form-error" style="display:none;"></div>"""

LOAD_ANCHOR = """    document.getElementById('display-name').value = p.display_name !== p.username ? p.display_name : '';
    document.getElementById('bio').value           = p.bio || '';"""

LOAD_NEW = """    document.getElementById('display-name').value = p.display_name !== p.username ? p.display_name : '';
    document.getElementById('bio').value           = p.bio || '';
    if (p.connections) {
      document.getElementById('twitch').value  = p.connections.twitch_url ? p.connections.twitch_url : '';
      document.getElementById('spotify').value = p.connections.spotify_url ? p.connections.spotify_url : '';
    }"""

SAVE_ANCHOR = """  if (ok) {
    const f = new FormData();
    f.append('bio', bio);
    const r = await fetch('/api/profile/bio', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }"""

SAVE_NEW = """  if (ok) {
    const f = new FormData();
    f.append('bio', bio);
    const r = await fetch('/api/profile/bio', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }

  const twitch  = document.getElementById('twitch').value.trim();
  const spotify = document.getElementById('spotify').value.trim();

  if (ok) {
    const f = new FormData();
    f.append('twitch', twitch);
    const r = await fetch('/api/profile/twitch', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }

  if (ok) {
    const f = new FormData();
    f.append('spotify', spotify);
    const r = await fetch('/api/profile/spotify', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }"""


def apply_patch(content, anchor, new, label):
    if anchor not in content:
        print(f"ERROR: anchor for '{label}' not found. Aborting before any write.")
        return None
    return content.replace(anchor, new, 1)


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'id="twitch"' in content:
        print("Already patched — no changes made.")
        return

    original = content

    content = apply_patch(content, FORM_ANCHOR, FORM_NEW, "form fields")
    if content is None:
        return

    content = apply_patch(content, LOAD_ANCHOR, LOAD_NEW, "prefill on load")
    if content is None:
        return

    content = apply_patch(content, SAVE_ANCHOR, SAVE_NEW, "save logic")
    if content is None:
        return

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched templates/profile_edit.html successfully.")


if __name__ == "__main__":
    main()
