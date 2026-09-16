"""
patch_add_chat_barter_nav.py

Adds two nav links to templates/base.html:
1. "Chat" -> /chat (the new public chat room)
2. "Barter Trade" -> the Gleaning project's barter page (external link,
   since Gleaning is a separate deployment for now — full merge into
   The Commons is a future, larger project)

Run once from your project root:
    python3 patch_add_chat_barter_nav.py
"""

PATH = "templates/base.html"

ANCHOR = '''      <a href="/explore" style="color:rgba(255,255,255,0.9);text-decoration:none;padding:14px 24px;font-size:16px;border-bottom:1px solid rgba(255,255,255,0.06);">Explore</a>'''

NEW = '''      <a href="/explore" style="color:rgba(255,255,255,0.9);text-decoration:none;padding:14px 24px;font-size:16px;border-bottom:1px solid rgba(255,255,255,0.06);">Explore</a>
      <a href="/chat" style="color:rgba(255,255,255,0.9);text-decoration:none;padding:14px 24px;font-size:16px;border-bottom:1px solid rgba(255,255,255,0.06);">Chat</a>
      <a href="https://gleaning.onrender.com/barter" target="_blank" rel="noopener noreferrer" style="color:rgba(255,255,255,0.9);text-decoration:none;padding:14px 24px;font-size:16px;border-bottom:1px solid rgba(255,255,255,0.06);">Barter Trade</a>'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'href="/chat"' in content:
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
