"""
patch_index_post_translate.py

1. Adds a unique id to each post's content div (post-content-{{ post.id }}).
2. Adds a "Translate" button to post-actions in templates/index.html,
   using Jinja's tojson filter to safely pass post content into the
   onclick JS call (handles quotes/newlines/HTML safely).

Run once from your project root:
    python3 patch_index_post_translate.py
"""

PATH = "templates/index.html"

CONTENT_ANCHOR = """        <div class="post-content">{{ post.content | replace("\\n", "<br>") }}</div>"""
CONTENT_NEW = """        <div class="post-content" id="post-content-{{ post.id }}">{{ post.content | replace("\\n", "<br>") }}</div>"""

ACTIONS_ANCHOR = """          <button onclick="vote({{ post.id }}, 1, this)" class="vote-btn {% if post.id in voted_post_ids %}voted{% endif %}" style="font-size:15px;background:none;border:none;color:var(--muted);">{% if post.id in voted_post_ids %}❤️{% else %}🤍{% endif %} <span id="score-{{ post.id }}">{{ post.community_score | int }}</span></button>
          <span style="font-size:14px;color:var(--muted);">💬 <span id="comment-count-{{ post.id }}">0</span></span>"""

ACTIONS_NEW = """          <button onclick="vote({{ post.id }}, 1, this)" class="vote-btn {% if post.id in voted_post_ids %}voted{% endif %}" style="font-size:15px;background:none;border:none;color:var(--muted);">{% if post.id in voted_post_ids %}❤️{% else %}🤍{% endif %} <span id="score-{{ post.id }}">{{ post.community_score | int }}</span></button>
          <button onclick='translatePost({{ post.id }}, {{ (post.content | replace("\\n", "<br>")) | tojson }}, {{ post.content | tojson }})' class="vote-btn" style="font-size:13px;background:none;border:none;color:var(--muted);">🌐 Translate</button>
          <span style="font-size:14px;color:var(--muted);">💬 <span id="comment-count-{{ post.id }}">0</span></span>"""


def apply_patch(content, anchor, new, label):
    count = content.count(anchor)
    if count == 0:
        print(f"ERROR: anchor for '{label}' not found. Aborting before any write.")
        return None
    if count > 1:
        print(f"ERROR: anchor for '{label}' matched {count} times (expected 1). Aborting — needs manual review.")
        return None
    return content.replace(anchor, new, 1)


def main():
    with open(PATH, "r") as f:
        content = f.read()

    if 'id="post-content-{{ post.id }}"' in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, CONTENT_ANCHOR, CONTENT_NEW, "post content id")
    if content2 is None:
        return

    content3 = apply_patch(content2, ACTIONS_ANCHOR, ACTIONS_NEW, "post translate button")
    if content3 is None:
        return

    with open(PATH, "w") as f:
        f.write(content3)

    print("Patched templates/index.html successfully.")


if __name__ == "__main__":
    main()
