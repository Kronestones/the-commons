"""
patch_add_explore_nav.py

Adds an "Explore" link to the slide-out nav menu in templates/base.html,
right after "Feed", pointing to /explore (the new news-outlets browse page).

Run once from your project root:
    python3 patch_add_explore_nav.py
"""

PATH = "templates/base.html"

ANCHOR = '''      <a href="/" style="color:rgba(255,255,255,0.9);text-decoration:none;padding:14px 24px;font-size:16px;border-bottom:1px solid rgba(255,255,255,0.06);">Feed</a>'''

NEW = '''      <a href="/" style="color:rgba(255,255,255,0.9);text-decoration:none;padding:14px 24px;font-size:16px;border-bottom:1px solid rgba(255,255,255,0.06);">Feed</a>
      <a href="/explore" style="color:rgba(255,255,255,0.9);text-decoration:none;padding:14px 24px;font-size:16px;border-bottom:1px solid rgba(255,255,255,0.06);">Explore</a>'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'href="/explore"' in content:
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

    print("Patched templates/base.html successfully.")


if __name__ == "__main__":
    main()
