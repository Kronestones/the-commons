"""
patch_profile_edit_bluesky_tiktok.py

Adds Bluesky and TikTok input fields to templates/profile_edit.html,
right after the YouTube field, matching its exact pattern (label,
input, prefill-on-load, save-on-submit).

Run once from your project root:
    python3 patch_profile_edit_bluesky_tiktok.py
"""

PATH = "templates/profile_edit.html"

FORM_ANCHOR = '''    <input type="text" id="youtube" placeholder="Paste a video or channel link">
    </label>'''

FORM_NEW = '''    <input type="text" id="youtube" placeholder="Paste a video or channel link">
    </label>

    <label>Bluesky <small>(handle or profile link — leave blank to remove)</small>
      <input type="text" id="bluesky" placeholder="e.g. yourname.bsky.social">
    </label>

    <label>TikTok <small>(username or profile link — leave blank to remove)</small>
      <input type="text" id="tiktok" placeholder="e.g. yourusername or https://tiktok.com/@yourusername">
    </label>'''

LOAD_ANCHOR = '''    document.getElementById('youtube').value = p.connections.youtube_video_url ? p.connections.youtube_video_url : (p.connections.youtube_channel_url ? p.connections.youtube_channel_url : '');'''

LOAD_NEW = '''    document.getElementById('youtube').value = p.connections.youtube_video_url ? p.connections.youtube_video_url : (p.connections.youtube_channel_url ? p.connections.youtube_channel_url : '');
    document.getElementById('bluesky').value = p.connections.bluesky_url ? p.connections.bluesky_url : '';
    document.getElementById('tiktok').value = p.connections.tiktok_url ? p.connections.tiktok_url : '';'''

SAVE_VAR_ANCHOR = '''  const youtube = document.getElementById('youtube').value.trim();'''

SAVE_VAR_NEW = '''  const youtube = document.getElementById('youtube').value.trim();
  const bluesky = document.getElementById('bluesky').value.trim();
  const tiktok = document.getElementById('tiktok').value.trim();'''

SAVE_CALL_ANCHOR = '''    f.append('youtube', youtube);
    const r = await fetch('/api/profile/youtube', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }'''

SAVE_CALL_NEW = '''    f.append('youtube', youtube);
    const r = await fetch('/api/profile/youtube', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }

  if (ok) {
    const f = new FormData();
    f.append('bluesky', bluesky);
    const r = await fetch('/api/profile/bluesky', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
  }

  if (ok) {
    const f = new FormData();
    f.append('tiktok', tiktok);
    const r = await fetch('/api/profile/tiktok', {
      method: 'POST', headers: { 'Authorization': 'Bearer ' + token }, body: f
    });
    const d = await r.json();
    if (!d.ok) { ok = false; msgEl.textContent = d.error; msgEl.style.display = ''; }
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

    if 'id="bluesky"' in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, FORM_ANCHOR, FORM_NEW, "form fields")
    if content2 is None:
        return

    content3 = apply_patch(content2, LOAD_ANCHOR, LOAD_NEW, "prefill on load")
    if content3 is None:
        return

    content4 = apply_patch(content3, SAVE_VAR_ANCHOR, SAVE_VAR_NEW, "save variables")
    if content4 is None:
        return

    content5 = apply_patch(content4, SAVE_CALL_ANCHOR, SAVE_CALL_NEW, "save API calls")
    if content5 is None:
        return

    with open(PATH, "w") as f:
        f.write(content5)

    print("Patched templates/profile_edit.html successfully.")


if __name__ == "__main__":
    main()
