"""
patch_index_use_linkify.py

Switches templates/index.html's post-content rendering to use the new
linkify filter, so URLs become clickable links on the feed page.

Must be run AFTER patch_add_linkify_filter.py.

Run once from your project root:
    python3 patch_index_use_linkify.py
"""

PATH = "templates/index.html"

ANCHOR = '''<div class="post-content" id="post-content-{{ post.id }}">{{ post.content | replace("\\n", "<br>") }}</div>'''

NEW = '''<div class="post-content" id="post-content-{{ post.id }}">{{ post.content | linkify | replace("\\n", "<br>") | safe }}</div>'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "| linkify | replace" in content:
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
