"""
patch_wire_media_embeds_profile.py

Wires the already-existing extractMediaEmbeds() function (defined in
static/js/main.js but never called anywhere) into profile.html's post
rendering, so pasted Twitch/Spotify/YouTube links in post text
actually auto-embed.

Run once from your project root:
    python3 patch_wire_media_embeds_profile.py
"""

PATH = "templates/profile.html"

ANCHOR = '''        <div class="post-content" id="post-content-${post.id}">${typeof linkify === 'function' ? linkify(post.content) : post.content}</div>'''

NEW = '''        <div class="post-content" id="post-content-${post.id}">${typeof linkify === 'function' ? linkify(post.content) : post.content}</div>
        ${typeof extractMediaEmbeds === 'function' ? extractMediaEmbeds(post.content) : ''}'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "extractMediaEmbeds(post.content)" in content:
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
