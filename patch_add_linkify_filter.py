"""
patch_add_linkify_filter.py

Adds a server-side linkify() function registered as a Jinja filter,
so URLs in post content become clickable links on the feed page
(templates/index.html), matching what the JS linkify() already does
on profile.html.

Run once from your project root:
    python3 patch_add_linkify_filter.py
"""

PATH = "main.py"

ANCHOR = '''templates = Jinja2Templates(directory="templates")'''

NEW = '''templates = Jinja2Templates(directory="templates")

import re as _re
import html as _html

_URL_RE = _re.compile(r'(https?://[^\\s<>"{}|\\\\^`\\[\\]]+)')

def _linkify_html(text: str) -> str:
    """Escape HTML, then wrap bare URLs in clickable <a> tags."""
    if not text:
        return ""
    escaped = _html.escape(text)
    return _URL_RE.sub(
        r'<a href="\\1" target="_blank" rel="noopener noreferrer" style="color:var(--green-dark);word-break:break-all;">\\1</a>',
        escaped
    )

templates.env.filters["linkify"] = _linkify_html'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'templates.env.filters["linkify"]' in content:
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

    print("Patched main.py successfully.")


if __name__ == "__main__":
    main()
