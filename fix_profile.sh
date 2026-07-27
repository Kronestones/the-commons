#!/data/data/com.termux/files/usr/bin/bash
# fix_profile.sh — The Commons profile page fix
# Fixes: post images not rendering, comments absent, like/heart state wrong
# Run from ~/the_commons

set -e

if [ ! -f "main.py" ] || [ ! -f "templates/profile.html" ] || [ ! -f "commons/features.py" ]; then
    echo "❌ Run this from the_commons project root (main.py not found here)."
    exit 1
fi

echo "📦 Backing up files..."
cp commons/features.py commons/features.py.bak
cp templates/profile.html templates/profile.html.bak
echo "   -> commons/features.py.bak"
echo "   -> templates/profile.html.bak"

# ── Fix 1: commons/features.py — add voted_post_ids + media_path + user_voted ──
echo "🔧 Patching commons/features.py..."

python3 << 'PYEOF'
import re

path = "commons/features.py"
with open(path, "r") as f:
    src = f.read()

old_stats_block = '''        # Creator stats
        total_likes = db.query(func.count(CommunityVote.id)).filter(
            CommunityVote.post_id.in_([p.id for p in posts])
        ).scalar() or 0'''

new_stats_block = '''        # Creator stats
        total_likes = db.query(func.count(CommunityVote.id)).filter(
            CommunityVote.post_id.in_([p.id for p in posts])
        ).scalar() or 0

        # Which of these posts has the viewer already voted/liked?
        voted_post_ids = set()
        if viewer:
            votes = db.query(CommunityVote).filter(
                CommunityVote.user_id == viewer.id,
                CommunityVote.post_id.in_([p.id for p in posts])
            ).all()
            voted_post_ids = {v.post_id for v in votes}'''

if old_stats_block not in src:
    print("❌ Could not find the 'Creator stats' block in features.py — aborting this patch.")
    raise SystemExit(1)

src = src.replace(old_stats_block, new_stats_block, 1)

old_posts_block = '''            "posts": [
                {
                    "id":              p.id,
                    "content":         p.content[:100],
                    "post_type":       p.post_type.value,
                    "community_score": p.community_score,
                    "view_count":      p.view_count,
                    "published_at":    p.published_at.isoformat() if p.published_at else None,
                }
                for p in posts
            ]'''

new_posts_block = '''            "posts": [
                {
                    "id":              p.id,
                    "content":         p.content,
                    "post_type":       p.post_type.value,
                    "media_path":      p.media_path,
                    "community_score": p.community_score,
                    "view_count":      p.view_count,
                    "published_at":    p.published_at.isoformat() if p.published_at else None,
                    "user_voted":      p.id in voted_post_ids,
                }
                for p in posts
            ]'''

if old_posts_block not in src:
    print("⚠️  Exact 'posts' block not found — trying whitespace-flexible match...")
    pattern = re.compile(
        r'"posts":\s*\[\s*\{\s*'
        r'"id":\s*p\.id,\s*'
        r'"content":\s*p\.content(\[:100\])?,\s*'
        r'"post_type":\s*p\.post_type\.value,\s*'
        r'("media_path":\s*p\.media_path,\s*)?'
        r'"community_score":\s*p\.community_score,\s*'
        r'"view_count":\s*p\.view_count,\s*'
        r'"published_at":\s*p\.published_at\.isoformat\(\) if p\.published_at else None,\s*'
        r'("user_voted":\s*p\.id in voted_post_ids,\s*)?'
        r'\}\s*'
        r'for p in posts\s*'
        r'\]',
        re.MULTILINE
    )
    if not pattern.search(src):
        print("❌ Could not locate the posts list block automatically.")
        print("   Please paste the file section around 'posts': [ and I will give you")
        print("   a manual patch instead.")
        raise SystemExit(1)
    src = pattern.sub(new_posts_block.strip(), src, count=1)
else:
    src = src.replace(old_posts_block, new_posts_block, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ commons/features.py patched.")
PYEOF

# ── Fix 2: templates/profile.html — rewrite post card + trigger comments ──
echo "🔧 Patching templates/profile.html..."

python3 << 'PYEOF'
path = "templates/profile.html"
with open(path, "r") as f:
    src = f.read()

old_card = '''    postsEl.innerHTML = p.posts.map(post => `
      <div class="post-card" id="post-${post.id}">
        <div class="post-header">
          <span class="post-author">@${p.username}</span>
          <span class="post-time">${post.published_at ? new Date(post.published_at).toLocaleDateString('en-US',{month:'short',day:'numeric'}) : ''}</span>
        </div>
        <div class="post-content">${post.content}</div>
        <div class="post-actions">
          <button onclick="vote(${post.id}, 1, this)" class="vote-btn">🤍</button>
          <span class="community-score">${Math.round(post.community_score)}</span>
          ${isOwn ? '<button onclick="deletePost(' + post.id + ', this)" class="delete-btn">Delete</button>' : ''}
        </div>
      </div>
    `).join('');'''

new_card = '''    postsEl.innerHTML = p.posts.map(post => `
      <div class="post-card" data-post-id="${post.id}" id="post-${post.id}">
        <div class="post-header">
          <span class="post-author">@${p.username}</span>
          <span class="post-time">${post.published_at ? new Date(post.published_at).toLocaleDateString('en-US',{month:'short',day:'numeric'}) : ''}</span>
        </div>
        <div class="post-content">${typeof linkify === 'function' ? linkify(post.content) : post.content}</div>
        ${post.media_path ? `<img src="${post.media_path.startsWith('http') ? post.media_path : '/media/' + post.media_path}" style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;object-fit:cover;">` : ''}
        <div class="post-actions">
          <button onclick="vote(${post.id}, 1, this)" class="vote-btn ${post.user_voted ? 'voted' : ''}">${post.user_voted ? '❤️' : '🤍'} <span id="score-${post.id}">${Math.round(post.community_score)}</span></button>
          ${isOwn ? '<button onclick="deletePost(' + post.id + ', this)" class="delete-btn">Delete</button>' : ''}
        </div>
        <div id="comments-${post.id}" style="margin-top:8px;">
          <div id="comment-list-${post.id}" style="margin-bottom:8px;"></div>
          <div style="display:flex;gap:8px;">
            <input id="comment-input-${post.id}" type="text" placeholder="Write a comment..."
              style="flex:1;padding:8px 12px;border:1px solid var(--border);border-radius:20px;font-size:14px;"
              onkeydown="if(event.key==='Enter'){submitComment(${post.id})}">
            <button onclick="submitComment(${post.id})" class="vote-btn" style="padding:8px 14px;font-size:13px;">Post</button>
          </div>
        </div>
      </div>
    `).join('');

    // Load comments for the freshly-rendered profile posts
    if (typeof autoLoadComments === 'function') {
      setTimeout(autoLoadComments, 100);
    }'''

if old_card not in src:
    print("❌ Could not find the exact post-card block in profile.html.")
    print("   The file may have changed since last review. Aborting this patch —")
    print("   features.py changes are still applied. Paste profile.html again")
    print("   and I'll hand-patch it.")
    raise SystemExit(1)

src = src.replace(old_card, new_card, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/profile.html patched.")
PYEOF

echo ""
echo "🎉 Done. Review the diffs with:"
echo "   diff commons/features.py.bak commons/features.py"
echo "   diff templates/profile.html.bak templates/profile.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix profile page: images, comments, like state'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp commons/features.py.bak commons/features.py"
echo "   cp templates/profile.html.bak templates/profile.html"
