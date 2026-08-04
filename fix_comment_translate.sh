#!/data/data/com.termux/files/usr/bin/bash
# fix_comment_translate.sh — Add tap-to-translate to comments using the
# existing /api/translate endpoint (already built, just not wired to comments).
# Run from ~/the_commons

set -e

if [ ! -f "static/js/main.js" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up static/js/main.js..."
cp static/js/main.js static/js/main.js.bak3
echo "   -> static/js/main.js.bak3"

python3 << 'PYEOF'
path = "static/js/main.js"
with open(path, "r") as f:
    src = f.read()

old = '''  commentList.innerHTML += shown.map(c => `
    <div style="padding:4px 0;font-size:14px;">
      <strong style="font-size:13px;">@${c.author}</strong>
      <span style="margin-left:6px;">${c.content}</span>
      <span style="margin-left:6px;font-size:11px;color:var(--muted);">${formatTime(c.created_at)}</span>
      ${c.author === username ? `<span onclick="deleteComment(${c.id}, ${postId})" style="color:var(--muted);font-size:11px;cursor:pointer;margin-left:8px;">✕</span>` : ''}
    </div>
  `).join('');
}'''

new = '''  commentList.innerHTML += shown.map(c => `
    <div style="padding:4px 0;font-size:14px;">
      <strong style="font-size:13px;">@${c.author}</strong>
      <span id="comment-text-${c.id}" style="margin-left:6px;">${c.content}</span>
      <span onclick="translateComment(${c.id}, ${JSON.stringify(c.content)})" style="margin-left:6px;font-size:11px;color:var(--green-dark);cursor:pointer;text-decoration:underline;">Translate</span>
      <span style="margin-left:6px;font-size:11px;color:var(--muted);">${formatTime(c.created_at)}</span>
      ${c.author === username ? `<span onclick="deleteComment(${c.id}, ${postId})" style="color:var(--muted);font-size:11px;cursor:pointer;margin-left:8px;">✕</span>` : ''}
    </div>
  `).join('');
}

// ── Translate ─────────────────────────────────────────────────────────────────
const commentOriginals = {};

async function translateComment(commentId, originalText) {
  const textEl = document.getElementById('comment-text-' + commentId);
  if (!textEl) return;

  if (commentOriginals[commentId]) {
    textEl.textContent = commentOriginals[commentId];
    delete commentOriginals[commentId];
    return;
  }

  const targetLang = (navigator.language || 'en').split('-')[0];
  const token = getToken();
  const form = new FormData();
  form.append('text', originalText);
  form.append('target_language', targetLang);

  try {
    const res = await fetch('/api/translate', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + token },
      body: form
    });
    const data = await res.json();
    if (data.ok) {
      commentOriginals[commentId] = originalText;
      textEl.textContent = data.translated_text;
    } else {
      showMessage(data.error || 'Could not translate.', true);
    }
  } catch(e) {
    showMessage('Translation unavailable right now.', true);
  }
}'''

if old not in src:
    print("❌ Could not find the loadInlineComments rendering block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ static/js/main.js patched — comments now have a 'Translate' tap using the existing /api/translate endpoint.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff static/js/main.js.bak3 static/js/main.js"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Add tap-to-translate for comments (accessibility for non-English speakers)'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp static/js/main.js.bak3 static/js/main.js"
