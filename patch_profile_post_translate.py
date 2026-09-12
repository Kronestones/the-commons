"""
patch_profile_post_translate.py

1. Adds a unique id to each post's content div (post-content-${id}),
   needed so translatePost() can target the right element.
2. Adds a "Translate" button to post-actions, next to vote/delete.

Run once from your project root:
    python3 patch_profile_post_translate.py
"""

PATH = "templates/profile.html"

CONTENT_ANCHOR = """        <div class="post-content">${typeof linkify === 'function' ? linkify(post.content) : post.content}</div>"""
CONTENT_NEW = """        <div class="post-content" id="post-content-${post.id}">${typeof linkify === 'function' ? linkify(post.content) : post.content}</div>"""

ACTIONS_ANCHOR = """          <button onclick="vote(${post.id}, 1, this)" class="vote-btn ${post.user_voted ? 'voted' : ''}">${post.user_voted ? '❤️' : '🤍'} <span id="score-${post.id}">${Math.round(post.community_score)}</span></button>
          ${isOwn ? '<button onclick="deletePost(' + post.id + ', this)" class="delete-btn">Delete</button>' : ''}"""

ACTIONS_NEW = """          <button onclick="vote(${post.id}, 1, this)" class="vote-btn ${post.user_voted ? 'voted' : ''}">${post.user_voted ? '❤️' : '🤍'} <span id="score-${post.id}">${Math.round(post.community_score)}</span></button>
          <button onclick="translatePost(${post.id}, ${JSON.stringify(typeof linkify === 'function' ? linkify(post.content) : post.content)}, ${JSON.stringify(post.content)})" class="vote-btn" style="background:none;">🌐 Translate</button>
          ${isOwn ? '<button onclick="deletePost(' + post.id + ', this)" class="delete-btn">Delete</button>' : ''}"""


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

    if 'id="post-content-' in content:
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

    print("Patched templates/profile.html successfully.")


if __name__ == "__main__":
    main()
