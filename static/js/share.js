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
