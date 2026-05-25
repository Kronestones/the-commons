/**
 * main.js — The Commons
 *
 * Handles auth state, nav updates, toasts, and shared UI.
 * No tracking. No analytics. No dark patterns.
 * Clean and purposeful.
 *
 * — Architect Founder Krone · The Commons · 2026
 */

// ── Auth State ────────────────────────────────────────────────────────────────

function getCookie(name) {
  const v = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return v ? v.pop() : '';
}
function getToken() {
  return getCookie('token') || localStorage.getItem('token') || '';
}
function getUsername() { return localStorage.getItem('username'); }
function isLoggedIn()  { return !!getToken(); }

function logout() {
  try {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.clear();
  } catch(e) {}
  window.location.href = '/login';
}

// ── Nav ───────────────────────────────────────────────────────────────────────

function updateNav() {
  const navUser = document.getElementById('nav-user');
  if (!navUser) return;

  if (isLoggedIn()) {
    navUser.innerHTML = `
      <a href="/profile/${getUsername()}" class="nav-username">@${getUsername()}</a>
      <button onclick="logout()" class="nav-logout">Sign out</button>
    `;
    // Show composer if on home page
    const composer = document.getElementById('composer');
    if (composer) composer.style.display = 'block';
  } else {
    navUser.innerHTML = `
      <a href="/login">Sign in</a>
      <a href="/register" class="nav-join">Join</a>
    `;
  }
}

// ── Toast Messages ────────────────────────────────────────────────────────────

function showMessage(text, isError = false) {
  // Remove any existing toast
  const existing = document.querySelector('.message-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = 'message-toast' + (isError ? ' error' : '');
  toast.textContent = text;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ── Algorithm Mode ────────────────────────────────────────────────────────────

async function setAlgorithmMode(mode) {
  const token = getToken();
  if (!token) return;
  const form = new FormData();
  form.append('mode', mode);
  const res = await fetch('/api/user/algorithm-mode', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + token },
    body: form
  });
  const data = await res.json();
  if (data.ok) {
    showMessage(`Feed mode set to: ${mode}`);
    setTimeout(() => location.reload(), 1000);
  }
}

// ── Feed Reasons ──────────────────────────────────────────────────────────────

function addFeedReasons() {
  // Transparent mode: show why each post appears
  document.querySelectorAll('.post-card[data-reason]').forEach(card => {
    const reason = card.dataset.reason;
    if (reason) {
      const reasonEl = document.createElement('p');
      reasonEl.className = 'post-reason';
      reasonEl.textContent = reason;
      card.querySelector('.post-content').before(reasonEl);
    }
  });
}

// ── Infinite Scroll ───────────────────────────────────────────────────────────

let feedOffset = 20;
let loadingMore = false;

async function loadMorePosts() {
  if (loadingMore || !isLoggedIn()) return;
  const feed = document.getElementById('feed');
  if (!feed) return;

  loadingMore = true;
  const token = getToken();

  const res  = await fetch(`/api/feed?limit=20&offset=${feedOffset}`, {
    headers: { 'Authorization': 'Bearer ' + token }
  });
  const data = await res.json();

  if (data.ok && data.feed.length > 0) {
    data.feed.forEach(post => {
      const card = document.createElement('div');
      card.className = 'post-card';
      card.setAttribute('data-post-id', post.id);
      card.id = 'post-' + post.id;
      card.innerHTML = `
        <div class="post-header">
          <span class="post-author">@${post.author}</span>
          <span class="post-time">${formatTime(post.published_at)}</span>
        </div>
        ${post.reason ? `<p class="post-reason">${post.reason}</p>` : ''}
        <div class="post-content">${linkify(post.content)}</div>
        <div class="post-actions">
          <button onclick="vote(${post.id}, 1, this)" class="vote-btn ${post.user_voted ? 'voted' : ''}">${post.user_voted ? '❤️' : '🤍'}</button>
          <span class="community-score">${Math.round(post.community_score)}</span>
          <button onclick="toggleComments(${post.id})" class="vote-btn" style="background:none;color:var(--muted);font-size:13px;padding:4px 8px;">💬 Comment</button>
          ${post.author === getUsername() ? `<button onclick="deletePost(${post.id}, this)" class="delete-btn">Delete</button>` : ''}
        </div>
      `;
      feed.appendChild(card);
    });
    feedOffset += data.feed.length;
  }

  loadingMore = false;
}

// Scroll detection for infinite feed
window.addEventListener('scroll', () => {
  if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 200) {
    loadMorePosts();
  }
});

// ── Utilities ─────────────────────────────────────────────────────────────────

function escapeHtml(text) {
  const div = document.createElement('div');
  div.appendChild(document.createTextNode(text || ''));
  return div.innerHTML;
}

function formatTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const now  = new Date();
  const diff = Math.floor((now - date) / 1000);
  if (diff < 60)   return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return date.toLocaleDateString();
}

// ── Post Actions ──────────────────────────────────────────────────────────────

async function deletePost(postId, btn) {
  if (!confirm('Delete this post?')) return;
  const token = getToken();
  const res   = await fetch(`/api/posts/${postId}`, {
    method:  'DELETE',
    headers: { 'Authorization': 'Bearer ' + token }
  });
  const data = await res.json();
  if (data.ok) {
    btn.closest('.post-card').remove();
  } else {
    showMessage(data.error || 'Could not delete post.', true);
  }
}

async function deleteProduct(productId, btn) {
  if (!confirm('Remove this listing?')) return;
  const token = getToken();
  const res   = await fetch(`/api/marketplace/products/${productId}`, {
    method:  'DELETE',
    headers: { 'Authorization': 'Bearer ' + token }
  });
  const data = await res.json();
  if (data.ok) {
    btn.closest('.product-card').remove();
  } else {
    showMessage(data.error || 'Could not remove listing.', true);
  }
}

async function vote(postId, value, btn) {
  const token = getToken();
  if (!token) { showMessage('Not logged in', true); return; }
  const form = new FormData();
  form.append('value', value);
  try {
    const res  = await fetch(`/api/posts/${postId}/vote`, {
      method:  'POST',
      headers: { 'Authorization': 'Bearer ' + token },
      body: form
    });
    if (res.status === 401) { showMessage('Session expired — please sign in again', true); return; }
    if (res.status === 422) { showMessage('Invalid request (422)', true); return; }
    const data = await res.json();
    if (data.ok) {
      if (btn) {
        btn.textContent = data.voted ? '❤️' : '🤍';
        btn.classList.toggle('voted', data.voted);
        const scoreEl = btn.parentElement.querySelector('.community-score');
        if (scoreEl) {
          const current = parseInt(scoreEl.textContent) || 0;
          scoreEl.textContent = data.voted ? current + 1 : current - 1;
        }
      }
    } else {
      showMessage(data.error || 'Could not vote', true);
    }
  } catch(e) {
    showMessage('Network error: ' + e.message, true);
  }
}

// ── Session Wellbeing Nudge ───────────────────────────────────────────────────
// Gentle notice after extended use. Not a hard stop. Just care.

let sessionStart = Date.now();
let nudgeShown   = false;

setInterval(() => {
  if (nudgeShown) return;
  const minutes = Math.floor((Date.now() - sessionStart) / 60000);
  if (minutes >= 45) {
    nudgeShown = true;
    const nudge = document.createElement('div');
    nudge.className = 'message-toast';
    nudge.style.background = '#2e7d4f';
    nudge.innerHTML = "You've been here a while. Everything good? 🌿";
    document.body.appendChild(nudge);
    setTimeout(() => nudge.remove(), 6000);
  }
}, 60000);

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  updateNav();
  addFeedReasons();
});

// ── Watch Time Tracking ───────────────────────────────────────────────────────
// Tells The Commons how much of a video you watched.
// Used only to understand your interests — never to maximize watch time.
// Transparent — you can see and reset this in your preferences.

function trackVideoWatch(postId, videoElement) {
  if (!videoElement || !isLoggedIn()) return;

  videoElement.addEventListener('timeupdate', () => {
    const percent = (videoElement.currentTime / videoElement.duration) * 100;
    if (percent >= 90 && !videoElement.dataset.completed) {
      videoElement.dataset.completed = 'true';
      sendWatchEvent(postId, 100);
    }
  });

  videoElement.addEventListener('pause', () => {
    const percent = (videoElement.currentTime / videoElement.duration) * 100;
    if (percent > 5) sendWatchEvent(postId, percent);
  });
}

async function sendWatchEvent(postId, watchPercent) {
  const token = getToken();
  if (!token) return;
  const form = new FormData();
  form.append('watch_percent', watchPercent);
  await fetch(`/api/posts/${postId}/watch`, {
    method:  'POST',
    headers: { 'Authorization': 'Bearer ' + token },
    body:    form
  });
}

// ── Record community vote as preference signal ────────────────────────────────
// When you vote on a post, it also updates your preference profile.

const originalVote = window.vote;
window.vote = async function(postId, value, btn) {
  await originalVote(postId, value, btn);
  // Voting is already handled — preference engine picks it up server-side
};

// ── Install App Banner ────────────────────────────────────────────────────────
// Shows a prompt to add The Commons to home screen on mobile
// Works on Android (PWA install) and iOS (manual instructions)

let deferredInstallPrompt = null;

// Capture the install prompt on Android
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;

  // Show banner if not dismissed before
  if (!localStorage.getItem('installDismissed')) {
    document.getElementById('install-banner').style.display = 'block';
  }
});

// Android — tap Add button
const installBtn = document.getElementById('install-btn');
if (installBtn) {
  installBtn.addEventListener('click', async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const result = await deferredInstallPrompt.userChoice;
      if (result.outcome === 'accepted') {
        document.getElementById('install-banner').style.display = 'none';
      }
      deferredInstallPrompt = null;
    }
  });
}

// Dismiss buttons
const dismissBtn = document.getElementById('install-dismiss');
if (dismissBtn) {
  dismissBtn.addEventListener('click', () => {
    document.getElementById('install-banner').style.display = 'none';
    localStorage.setItem('installDismissed', 'true');
  });
}

const iosDismiss = document.getElementById('ios-dismiss');
if (iosDismiss) {
  iosDismiss.addEventListener('click', () => {
    document.getElementById('ios-banner').style.display = 'none';
    localStorage.setItem('installDismissed', 'true');
  });
}

// iOS detection — show manual instructions
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
const isInStandaloneMode = window.matchMedia('(display-mode: standalone)').matches;

if (isIOS && !isInStandaloneMode && !localStorage.getItem('installDismissed')) {
  document.getElementById('ios-banner').style.display = 'block';
}

// Hide banner if already installed
if (isInStandaloneMode) {
  const banner = document.getElementById('install-banner');
  const iosBanner = document.getElementById('ios-banner');
  if (banner) banner.style.display = 'none';
  if (iosBanner) iosBanner.style.display = 'none';
}

// ── Show/Hide Password ────────────────────────────────────────────────────────
function togglePassword(inputId, btn) {
  const input = document.getElementById(inputId);
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = 'Hide';
  } else {
    input.type = 'password';
    btn.textContent = 'Show';
  }
}

// ── Auth Guard ────────────────────────────────────────────────────────────────
// Pages that don't require a token
const PUBLIC_PATHS = ['/login', '/register', '/codex', '/kinto'];
const LANDING_PAGE = '/register';

(function authGuard() {
  try {
    const path = window.location.pathname;
    const isPublic = PUBLIC_PATHS.some(p => path === p || path.startsWith(p + '/'));
    if (!isPublic && !getToken()) {
      document.body.style.visibility = 'hidden';
      window.location.href = '/login';
    } else {
      document.body.style.visibility = 'visible';
    }
  } catch(e) {
    document.body.style.visibility = 'visible';
  }
})();

// ── Mobile Nav ────────────────────────────────────────────────────────────────
function toggleNav() {
  const nav   = document.getElementById('nav-links');
  const btn   = document.getElementById('hamburger');
  const open  = nav.classList.toggle('nav-open');
  btn.textContent = open ? '✕' : '☰';
}

// ── Message Badge ─────────────────────────────────────────────────────────────
async function updateMessageBadge() {
  const token = getToken();
  if (!token) return;
  try {
    const [inboxRes, reqRes] = await Promise.all([
      fetch('/api/messages/inbox',    { headers: { 'Authorization': 'Bearer ' + token } }),
      fetch('/api/messages/requests', { headers: { 'Authorization': 'Bearer ' + token } })
    ]);
    const inbox = await inboxRes.json();
    const reqs  = await reqRes.json();
    const unread = (inbox.inbox  || []).filter(m => m.unread).length;
    const pending = (reqs.requests || []).length;
    const total = unread + pending;
    const badge = document.getElementById('msg-badge');
    if (badge) {
      if (total > 0) {
        badge.textContent = total > 9 ? '9+' : total;
        badge.style.display = 'block';
      } else {
        badge.style.display = 'none';
      }
    }
  } catch(e) {}
}

if (getToken()) {
  updateMessageBadge();
  setInterval(updateMessageBadge, 30000);
}

// ── Feed Info Card ────────────────────────────────────────────────────────────
function dismissFeedInfo() {
  const card = document.getElementById('feed-info-card');
  if (card) card.style.display = 'none';
  localStorage.setItem('feedInfoDismissed', 'true');
}

(function() {
  if (localStorage.getItem('feedInfoDismissed')) {
    const card = document.getElementById('feed-info-card');
    if (card) card.style.display = 'none';
  }
})();

// ── Comments ──────────────────────────────────────────────────────────────────
async function toggleComments(postId) {
  const existing = document.getElementById('comments-' + postId);
  if (existing) { existing.remove(); return; }

  const card = document.querySelector(`[data-post-id="${postId}"]`) ||
    document.getElementById('post-' + postId);
  if (!card) return;

  const box = document.createElement('div');
  box.id = 'comments-' + postId;
  box.style.cssText = 'border-top:1px solid var(--border);margin-top:10px;padding-top:10px;';
  box.innerHTML = '<p style="color:var(--muted);font-size:13px;">Loading...</p>';
  card.appendChild(box);

  await loadComments(postId);
}

async function loadComments(postId, showAll = false) {
  const token = getToken();
  const box = document.getElementById('comments-' + postId);
  if (!box) return;

  const res = await fetch('/api/posts/' + postId + '/comments', {
    headers: { 'Authorization': 'Bearer ' + token }
  });
  const data = await res.json();
  const comments = data.comments || [];
  const username = getUsername();

  // Update count on button
  const btn = document.getElementById('comments-btn-' + postId);
  if (btn) btn.textContent = '💬 ' + comments.length + ' Comment' + (comments.length !== 1 ? 's' : '');

  const preview = showAll ? comments : comments.slice(0, 2);
  const hasMore = !showAll && comments.length > 2;

  let html = '';
  if (comments.length) {
    html += preview.map(c => `
      <div style="padding:8px 0;border-bottom:1px solid var(--border);">
        <div style="display:flex;justify-content:space-between;align-items:center;">
          <strong style="font-size:13px;">@${c.author}</strong>
          <span style="font-size:11px;color:var(--muted);">${formatTime(c.created_at)}</span>
        </div>
        <p style="margin:4px 0;font-size:14px;">${c.content}</p>
        ${c.author === username ? `<button onclick="deleteComment(${c.id}, ${postId})" style="background:none;border:none;color:var(--muted);font-size:11px;cursor:pointer;padding:0;">Delete</button>` : ''}
      </div>
    `).join('');
    if (hasMore) {
      html += `<p onclick="loadComments(${postId}, true)" style="font-size:12px;color:var(--green-mid);cursor:pointer;margin:6px 0;">View all ${comments.length} comments</p>`;
    }
  } else {
    html += '<p style="color:var(--muted);font-size:13px;text-align:center;padding:8px 0;">No comments yet. Be the first.</p>';
  }

  html += `
    <div style="margin-top:10px;display:flex;gap:8px;">
      <input id="comment-input-${postId}" type="text" placeholder="Write a comment..."
        style="flex:1;padding:8px 12px;border:1px solid var(--border);border-radius:20px;font-size:14px;"
        onkeydown="if(event.key==='Enter'){submitComment(${postId})}">
      <button onclick="submitComment(${postId})" class="vote-btn" style="padding:8px 14px;font-size:13px;">Post</button>
    </div>
  `;

  box.innerHTML = html;
}

  html += `
    <div style="margin-top:10px;display:flex;gap:8px;">
      <input id="comment-input-${postId}" type="text" placeholder="Write a comment..."
        style="flex:1;padding:8px 12px;border:1px solid var(--border);border-radius:20px;font-size:14px;"
        onkeydown="if(event.key==='Enter'){submitComment(${postId})}">
      <button onclick="submitComment(${postId})" class="vote-btn" style="padding:8px 14px;font-size:13px;">Post</button>
    </div>
  `;

  box.innerHTML = html;
}

async function submitComment(postId) {
  const token = getToken();
  const input = document.getElementById('comment-input-' + postId);
  const content = input.value.trim();
  if (!content) return;
  const form = new FormData();
  form.append('content', content);
  const res = await fetch('/api/posts/' + postId + '/comments', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + token },
    body: form
  });
  const data = await res.json();
  if (data.ok) {
    input.value = '';
    loadComments(postId);
  } else {
    showMessage(data.error || 'Could not post comment.', true);
  }
}

async function deleteComment(commentId, postId) {
  if (!confirm('Delete this comment?')) return;
  const token = getToken();
  const form = new FormData();
  const res = await fetch('/api/comments/' + commentId, {
    method: 'DELETE',
    headers: { 'Authorization': 'Bearer ' + token },
    body: form
  });
  const data = await res.json();
  if (data.ok) loadComments(postId);
}

// ── Linkify ───────────────────────────────────────────────────────────────────
function linkify(text) {
  const urlRegex = /(https?:\/\/[^\s<>"{}|\\^`\[\]]+)/g;
  return escapeHtml(text).replace(urlRegex, '<a href="$1" target="_blank" rel="noopener noreferrer" style="color:var(--green-dark);word-break:break-all;">$1</a>');
}
