#!/data/data/com.termux/files/usr/bin/bash
# fix_comment_dates.sh — Add timestamps to comments (already returned by API, just not displayed)
# Run from ~/the_commons

set -e

if [ ! -f "static/js/main.js" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up static/js/main.js..."
cp static/js/main.js static/js/main.js.bak
echo "   -> static/js/main.js.bak"

python3 << 'PYEOF'
path = "static/js/main.js"
with open(path, "r") as f:
    src = f.read()

changes_made = 0

old_1 = '''  commentList.innerHTML += shown.map(c => `
    <div style="padding:4px 0;font-size:14px;">
      <strong style="font-size:13px;">@${c.author}</strong>
      <span style="margin-left:6px;">${c.content}</span>
      ${c.author === username ? `<span onclick="deleteComment(${c.id}, ${postId})" style="color:var(--muted);font-size:11px;cursor:pointer;margin-left:8px;">✕</span>` : ''}
    </div>
  `).join('');
}

async function loadAllComments(postId) {'''

new_1 = '''  commentList.innerHTML += shown.map(c => `
    <div style="padding:4px 0;font-size:14px;">
      <strong style="font-size:13px;">@${c.author}</strong>
      <span style="margin-left:6px;">${c.content}</span>
      <span style="margin-left:6px;font-size:11px;color:var(--muted);">${formatTime(c.created_at)}</span>
      ${c.author === username ? `<span onclick="deleteComment(${c.id}, ${postId})" style="color:var(--muted);font-size:11px;cursor:pointer;margin-left:8px;">✕</span>` : ''}
    </div>
  `).join('');
}

async function loadAllComments(postId) {'''

if old_1 in src:
    src = src.replace(old_1, new_1, 1)
    changes_made += 1
else:
    print("⚠️  Could not find loadInlineComments block — skipping this one.")

old_2 = '''  commentList.innerHTML = comments.map(c => `
    <div style="padding:4px 0;font-size:14px;">
      <strong style="font-size:13px;">@${c.author}</strong>
      <span style="margin-left:6px;">${c.content}</span>
      ${c.author === username ? `<span onclick="deleteComment(${c.id}, ${postId})" style="color:var(--muted);font-size:11px;cursor:pointer;margin-left:8px;">✕</span>` : ''}
    </div>
  `).join('');
}

async function loadComments(postId) {'''

new_2 = '''  commentList.innerHTML = comments.map(c => `
    <div style="padding:4px 0;font-size:14px;">
      <strong style="font-size:13px;">@${c.author}</strong>
      <span style="margin-left:6px;">${c.content}</span>
      <span style="margin-left:6px;font-size:11px;color:var(--muted);">${formatTime(c.created_at)}</span>
      ${c.author === username ? `<span onclick="deleteComment(${c.id}, ${postId})" style="color:var(--muted);font-size:11px;cursor:pointer;margin-left:8px;">✕</span>` : ''}
    </div>
  `).join('');
}

async function loadComments(postId) {'''

if old_2 in src:
    src = src.replace(old_2, new_2, 1)
    changes_made += 1
else:
    print("⚠️  Could not find loadAllComments block — skipping this one.")

old_3 = '''    html += comments.map(c => `
      <div style="padding:8px 0;border-bottom:1px solid var(--border);">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:13px;">@${c.author}</strong>
          <span style="font-size:11px;color:var(--muted);">${formatTime(c.created_at)}</span>
        </div>
        <p style="margin:4px 0;font-size:14px;">${c.content}</p>
        ${c.author === username ? `<button onclick="deleteComment(${c.id}, ${postId})" style="background:none;border:none;color:var(--muted);font-size:11px;cursor:pointer;padding:0;">Delete</button>` : ''}
      </div>
    `).join('');'''

if old_3 in src:
    print("ℹ️  loadComments() already displays formatTime(c.created_at) — no change needed there.")
else:
    print("⚠️  Could not find loadComments block in expected form — please check manually.")

with open(path, "w") as f:
    f.write(src)

print(f"✅ static/js/main.js patched — {changes_made} of 2 needed comment date additions applied.")
if changes_made < 2:
    print("⚠️  Not all patches applied — please review the file manually before deploying.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff static/js/main.js.bak static/js/main.js"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Add timestamps to comments (data already existed, now displayed)'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp static/js/main.js.bak static/js/main.js"
