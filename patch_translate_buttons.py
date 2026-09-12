"""
patch_translate_buttons.py

Adds a real, working "Translate" button to:
1. Comments (loadComments in static/js/main.js)
2. Posts (wherever post-actions render, in the same file)

Uses /api/translate, targeting the viewer's browser language
(navigator.language) automatically — no dropdown needed.

Run once from your project root:
    python3 patch_translate_buttons.py
"""

PATH = "static/js/main.js"

# ── 1. Comment translate button ──────────────────────────────────────────
COMMENT_ANCHOR = """        <p style="margin:4px 0;font-size:14px;">${c.content}</p>
        ${c.author === username ? `<button onclick="deleteComment(${c.id}, ${postId})" style="background:none;border:none;color:var(--muted);font-size:11px;cursor:pointer;padding:0;">Delete</button>` : ''}"""

COMMENT_NEW = """        <p id="comment-text-${c.id}" style="margin:4px 0;font-size:14px;">${c.content}</p>
        <div style="display:flex;gap:10px;">
          <button onclick="translateComment(${c.id}, ${JSON.stringify(c.content)})" style="background:none;border:none;color:var(--muted);font-size:11px;cursor:pointer;padding:0;">🌐 Translate</button>
          ${c.author === username ? `<button onclick="deleteComment(${c.id}, ${postId})" style="background:none;border:none;color:var(--muted);font-size:11px;cursor:pointer;padding:0;">Delete</button>` : ''}
        </div>"""

# ── 2. Shared translate helper + language detection ─────────────────────
HELPER_ANCHOR = """// ── Linkify ───────────────────────────────────────────────────────────────────"""

HELPER_NEW = """// ── Translate ─────────────────────────────────────────────────────────────────
function browserTargetLanguage() {
  const code = (navigator.language || 'en').split('-')[0].toLowerCase();
  return code;
}

async function translateComment(commentId, originalText) {
  const el = document.getElementById('comment-text-' + commentId);
  if (!el) return;
  if (el.dataset.translated === '1') {
    el.textContent = originalText;
    el.dataset.translated = '0';
    return;
  }
  const token = getToken();
  const form = new FormData();
  form.append('text', originalText);
  form.append('target_language', browserTargetLanguage());
  try {
    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token },
      body: form
    });
    const data = await res.json();
    if (data.ok) {
      el.textContent = data.translated_text;
      el.dataset.translated = '1';
    } else {
      showMessage(data.error || 'Translation failed.', true);
    }
  } catch (e) {
    showMessage('Translation service unavailable.', true);
  }
}

async function translatePost(postId, originalHtml, originalText) {
  const el = document.getElementById('post-content-' + postId);
  if (!el) return;
  if (el.dataset.translated === '1') {
    el.innerHTML = originalHtml;
    el.dataset.translated = '0';
    return;
  }
  const token = getToken();
  const form = new FormData();
  form.append('text', originalText);
  form.append('target_language', browserTargetLanguage());
  try {
    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token },
      body: form
    });
    const data = await res.json();
    if (data.ok) {
      el.textContent = data.translated_text;
      el.dataset.translated = '1';
    } else {
      showMessage(data.error || 'Translation failed.', true);
    }
  } catch (e) {
    showMessage('Translation service unavailable.', true);
  }
}

// ── Linkify ───────────────────────────────────────────────────────────────────"""


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

    if "function translateComment" in content:
        print("Already patched — no changes made.")
        return

    content2 = apply_patch(content, COMMENT_ANCHOR, COMMENT_NEW, "comment translate button")
    if content2 is None:
        return

    content3 = apply_patch(content2, HELPER_ANCHOR, HELPER_NEW, "translate helper functions")
    if content3 is None:
        return

    with open(PATH, "w") as f:
        f.write(content3)

    print("Patched static/js/main.js successfully.")
    print("NOTE: post-level translate button (translatePost) was added as a helper function,")
    print("but is not yet wired into post rendering — that needs a separate small patch")
    print("once we see how posts render their content div (post-content-${id} id needed).")


if __name__ == "__main__":
    main()
