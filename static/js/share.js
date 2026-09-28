// static/js/share.js: "Share" button handler (loaded site-wide from base.html after main.js)
async function sharePost(postId, btn) {
  if (typeof getToken !== 'function' || !getToken()) {
    window.location.href = '/login';
    return;
  }
  const caption = prompt('Add a comment to your share (optional):');
  if (caption === null) return; // cancelled

  const body = new URLSearchParams();
  body.append('caption', caption);
  try {
    const res = await fetch('/api/posts/' + postId + '/share', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Bearer ' + getToken(),
      },
      body: body.toString(),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      alert(data.error || data.detail || 'Could not share this post.');
      return;
    }
    if (btn) {
      btn.textContent = '\u2705 Shared';
      btn.disabled = true;
    }
  } catch (e) {
    alert('Could not share this post.');
  }
}

// Builds the "original post" box shown inside a share (used by the scrolling feed and profile pages).
function renderSharedPost(shared) {
  if (!shared) return '';
  if (!shared.available) {
    return '<div class="shared-post" style="border:1px dashed var(--border);border-radius:10px;padding:10px 12px;margin-top:8px;color:var(--muted);font-size:14px;">This post is no longer available.</div>';
  }
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const src = shared.media_path ? (shared.media_path.startsWith('http') ? shared.media_path : '/media/' + shared.media_path) : '';
  let media = '';
  if (src) {
    media = shared.post_type === 'video'
      ? '<video src="' + esc(src) + '" controls playsinline style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;background:#000;"></video>'
      : '<img src="' + esc(src) + '" style="width:100%;border-radius:8px;margin-top:8px;max-height:500px;object-fit:cover;">';
  }
  const body = (typeof linkify === 'function') ? linkify(shared.content) : esc(shared.content);
  return '<div class="shared-post" style="border:1px solid var(--border);border-radius:10px;padding:10px 12px;margin-top:8px;background:var(--green-light);">' +
    '<div class="post-header"><span class="post-author"><a href="/profile/' + encodeURIComponent(shared.author) + '" style="color:inherit;text-decoration:none;">@' + esc(shared.author) + '</a></span></div>' +
    '<div class="post-content">' + body + '</div>' + media + '</div>';
}
