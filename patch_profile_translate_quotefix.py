"""
patch_profile_translate_quotefix.py

Fixes a bug in the translate button added to templates/profile.html:
the onclick attribute used double quotes while JSON.stringify() also
produces double-quoted strings, so any post containing a " character
would break the button (the browser would think the attribute ended
early). This switches the onclick attribute to single quotes.

Run once from your project root, AFTER patch_profile_post_translate.py
has already been applied:
    python3 patch_profile_translate_quotefix.py
"""

PATH = "templates/profile.html"

BUGGY = '''<button onclick="translatePost(${post.id}, ${JSON.stringify(typeof linkify === 'function' ? linkify(post.content) : post.content)}, ${JSON.stringify(post.content)})" class="vote-btn" style="background:none;">🌐 Translate</button>'''

FIXED = """<button onclick='translatePost(${post.id}, ${JSON.stringify(typeof linkify === "function" ? linkify(post.content) : post.content)}, ${JSON.stringify(post.content)})' class="vote-btn" style="background:none;">🌐 Translate</button>"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if FIXED in content:
        print("Already fixed — no changes made.")
        return

    if BUGGY not in content:
        print("ERROR: expected buggy pattern not found. Either already fixed differently, or file changed — check manually before proceeding.")
        return

    count = content.count(BUGGY)
    if count > 1:
        print(f"ERROR: pattern matched {count} times (expected 1). Aborting — needs manual review.")
        return

    content = content.replace(BUGGY, FIXED, 1)

    with open(PATH, "w") as f:
        f.write(content)

    print("Fixed the quote-collision bug in templates/profile.html.")


if __name__ == "__main__":
    main()
