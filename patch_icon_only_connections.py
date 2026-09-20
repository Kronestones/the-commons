"""
patch_icon_only_connections.py

Simplifies the compact connection icons to icon-only — no green pill
background, no text label. Just the brand logo, slightly larger, with
the platform name kept as a title="" tooltip for accessibility.

Run once from your project root, AFTER patch_svg_connection_icons.py
has already been applied:
    python3 patch_icon_only_connections.py
"""

PATH = "templates/profile.html"

ANCHOR = '''      if (iconLinks.length) {
        html += '<div style="display:flex;gap:10px;flex-wrap:wrap;">';
        iconLinks.forEach(function(l) {
          html += '<a href="' + l.url + '" target="_blank" rel="noopener noreferrer" title="' + l.label + '" style="display:flex;align-items:center;gap:6px;padding:6px 12px;border-radius:16px;background:var(--green-mid, #2e7d52);color:white;text-decoration:none;font-size:13px;font-weight:600;">' + l.icon + ' ' + l.label + '</a>';
        });
        html += '</div>';
      }'''

NEW = '''      if (iconLinks.length) {
        html += '<div style="display:flex;gap:14px;flex-wrap:wrap;">';
        iconLinks.forEach(function(l) {
          html += '<a href="' + l.url + '" target="_blank" rel="noopener noreferrer" title="' + l.label + '" style="display:inline-flex;color:var(--green-dark, #2e7d52);">' + l.icon.replace('width="16" height="16"', 'width="24" height="24"').replace(/fill="white"/, 'fill="currentColor"') + '</a>';
        });
        html += '</div>';
      }'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'width="24" height="24"' in content:
        print("Already patched — no changes made.")
        return

    count = content.count(ANCHOR)
    if count == 0:
        print("ERROR: anchor not found. Aborting before any write.")
        return
    if count > 1:
        print(f"ERROR: anchor matched {count} times (expected 1). Aborting.")
        return

    content = content.replace(ANCHOR, NEW, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Patched templates/profile.html successfully.")


if __name__ == "__main__":
    main()
