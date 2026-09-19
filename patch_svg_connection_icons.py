"""
patch_svg_connection_icons.py

Replaces the emoji-based icons in the compact connection row with real
brand SVG icons (Simple Icons, CC0 licensed — free for commercial use,
no attribution required). Icons are embedded inline as SVG strings so
their fill color can be set to white against the green pill background.

Run once from your project root, AFTER patch_compact_connection_icons.py
has already been applied:
    python3 patch_svg_connection_icons.py
"""

PATH = "templates/profile.html"

ANCHOR = '''      const iconLinks = [];
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

NEW = '''      const SVG_ICONS = {
        youtube: '<svg viewBox="0 0 24 24" width="16" height="16" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>',
        bluesky: '<svg viewBox="0 0 24 24" width="16" height="16" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M5.202 2.857C7.954 4.922 10.913 9.11 12 11.358c1.087-2.247 4.046-6.436 6.798-8.501C20.783 1.366 24 .213 24 3.883c0 .732-.42 6.156-.667 7.037-.856 3.061-3.978 3.842-6.755 3.37 4.854.826 6.089 3.562 3.422 6.299-5.065 5.196-7.28-1.304-7.847-2.97-.104-.305-.152-.448-.153-.327 0-.121-.05.022-.153.327-.568 1.666-2.782 8.166-7.847 2.97-2.667-2.737-1.432-5.473 3.422-6.3-2.777.473-5.899-.308-6.755-3.369C.42 10.04 0 4.615 0 3.883c0-3.67 3.217-2.517 5.202-1.026"/></svg>',
        tiktok: '<svg viewBox="0 0 24 24" width="16" height="16" fill="white" xmlns="http://www.w3.org/2000/svg"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>'
      };

      const iconLinks = [];
      if (c.youtube_channel_url && !c.youtube_video_url) {
        iconLinks.push({ url: c.youtube_channel_url, icon: SVG_ICONS.youtube, label: 'YouTube' });
      }
      if (c.bluesky_url) {
        iconLinks.push({ url: c.bluesky_url, icon: SVG_ICONS.bluesky, label: 'Bluesky' });
      }
      if (c.tiktok_url) {
        iconLinks.push({ url: c.tiktok_url, icon: SVG_ICONS.tiktok, label: 'TikTok' });
      }
      if (iconLinks.length) {
        html += '<div style="display:flex;gap:10px;flex-wrap:wrap;">';
        iconLinks.forEach(function(l) {
          html += '<a href="' + l.url + '" target="_blank" rel="noopener noreferrer" title="' + l.label + '" style="display:flex;align-items:center;gap:6px;padding:6px 12px;border-radius:16px;background:var(--green-mid, #2e7d52);color:white;text-decoration:none;font-size:13px;font-weight:600;">' + l.icon + ' ' + l.label + '</a>';
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

    if "SVG_ICONS" in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, ANCHOR, NEW, "SVG icon swap")
    if content2 is None:
        return

    with open(PATH, "w") as f:
        f.write(content2)

    print("Patched templates/profile.html successfully.")


if __name__ == "__main__":
    main()
