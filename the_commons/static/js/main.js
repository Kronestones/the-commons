/**
 * main.js — The Commons
 *
 * Handles auth state, nav updates, toasts, and shared UI.
 * No tracking. No analytics. No dark patterns.
 * Clean and purposeful.
 *
 * — Sovereign Human T.L. Powers · The Commons · 2026
 */

// ── Auth State ────────────────────────────────────────────────────────────────

function getToken()    { return localStorage.getItem('token'); }
function getUsername() { return localStorage.getItem('username'); }
function isLoggedIn()  { return !!getToken(); }

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('username');
  window.location = '/';
}

// ── Nav ───────────────────────────────────────────────────────────────────────

function updateNav() {
  const navUser = document.getElementById('nav-user');
  if (!navUser) return;

  if (isLoggedIn()) {
    navUser.innerHTML = `
      <span class="nav-username">@${getUsername()}</span>
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
      card.innerHTML = `
        <div class="post-header">
          <span class="post-author">@${post.author}</span>
          <span class="post-time">${formatTime(post.published_at)}</span>
        </div>
        ${post.reason ? `<p class="post-reason">${post.reason}</p>` : ''}
        <div class="post-content">${escapeHtml(post.content)}</div>
        <div class="post-actions">
          <button onclick="vote(${post.id}, 1)" class="vote-btn">↑ Valuable</button>
          <span class="community-score">${Math.round(post.community_score)}</span>
          <button onclick="vote(${post.id}, -1)" class="vote-btn">↓</button>
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

async function vote(postId, value) {
  const token = getToken();
  if (!token) { window.location = '/login'; return; }
  const form = new FormData();
  form.append('value', value);
  const res  = await fetch(`/api/posts/${postId}/vote`, {
    method:  'POST',
    headers: { 'Authorization': 'Bearer ' + token },
    body: form
  });
  const data = await res.json();
  if (data.ok) showMessage(value === 1 ? 'Marked as valuable' : 'Noted');
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
window.vote = async function(postId, value) {
  await originalVote(postId, value);
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
