"""
patch_author_link_profile.py

Wraps the @username in each post (profile.html's JS-rendered posts)
in a link to /profile/{username}.

Run once from your project root:
    python3 patch_author_link_profile.py
"""

PATH = "templates/profile.html"

ANCHOR = """          <span class="post-author">@${p.username}</span>"""

NEW = """          <span class="post-author"><a href="/profile/${p.username}" style="color:inherit;text-decoration:none;">@${p.username}</a></span>"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'href="/profile/${p.username}"' in content:
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
