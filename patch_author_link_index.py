"""
patch_author_link_index.py

Wraps the @author name in each post (index.html feed) in a link to
/profile/{username}, so tapping it navigates to their profile.

Run once from your project root:
    python3 patch_author_link_index.py
"""

PATH = "templates/index.html"

ANCHOR = """          <span class="post-author">@{{ post.author.username if post.author else 'unknown' }}</span>"""

NEW = """          <span class="post-author">{% if post.author %}<a href="/profile/{{ post.author.username }}" style="color:inherit;text-decoration:none;">@{{ post.author.username }}</a>{% else %}@unknown{% endif %}</span>"""


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'href="/profile/{{ post.author.username }}"' in content:
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

    print("Patched templates/index.html successfully.")


if __name__ == "__main__":
    main()
