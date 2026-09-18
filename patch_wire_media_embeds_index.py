"""
patch_wire_media_embeds_index.py

Wires extractMediaEmbeds() into templates/index.html's post rendering
(the feed page). Since this content is Jinja-rendered server-side
rather than JS template literals, this calls extractMediaEmbeds via a
small inline script per post, using the post's ID to target the right
container — matching how post-content-{{ post.id }} already works.

Run once from your project root:
    python3 patch_wire_media_embeds_index.py
"""

PATH = "templates/index.html"

ANCHOR = '''        <div class="post-content" id="post-content-{{ post.id }}">{{ post.content | replace("\\n", "<br>") }}</div>'''

NEW = '''        <div class="post-content" id="post-content-{{ post.id }}">{{ post.content | replace("\\n", "<br>") }}</div>
        <div class="post-media-embed" id="post-media-embed-{{ post.id }}"></div>
        <script>
          (function() {
            var text = {{ post.content | tojson }};
            var target = document.getElementById('post-media-embed-{{ post.id }}');
            if (target && typeof extractMediaEmbeds === 'function') {
              target.innerHTML = extractMediaEmbeds(text);
            }
          })();
        </script>'''


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if "post-media-embed-" in content:
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
