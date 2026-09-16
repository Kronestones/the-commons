// static/js/chat.js
//
// Public chat room: polling-based updates, send, report, block.
// No WebSockets — matches your Render free-tier hosting constraints.

(function () {
  const POLL_INTERVAL_MS = 3500;

  const chatMessagesEl = document.getElementById('chatMessages');
  const chatLoadingEl = document.getElementById('chatLoading');
  const chatWindowEl = document.getElementById('chatWindow');
  const chatForm = document.getElementById('chatForm');
  const chatInput = document.getElementById('chatInput');
  const messageTemplate = document.getElementById('chatMessageTemplate');
  const dismissBtn = document.getElementById('dismissDisclaimer');
  const disclaimerEl = document.getElementById('chatDisclaimer');

  let knownMessageIds = new Set();
  let pollTimer = null;

  // --- Disclaimer dismiss (session-only, not permanent) -----------------
  // Per-tab memory var instead of localStorage/sessionStorage so this
  // works safely inside any embedded/artifact context too, and simply
  // re-shows on next full page load — intentional for a safety notice.
  let disclaimerDismissed = false;
  if (dismissBtn) {
    dismissBtn.addEventListener('click', () => {
      disclaimerDismissed = true;
      disclaimerEl.classList.add('chat-disclaimer-dismissed');
    });
  }

  function escapeForDisplay(str) {
    // Messages are already HTML-escaped server-side before storage,
    // but escape again defensively in case that ever changes.
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function formatTime(isoString) {
    const d = new Date(isoString);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function renderMessage(msg) {
    const node = messageTemplate.content.cloneNode(true);
    const el = node.querySelector('.chat-message');
    el.dataset.messageId = msg.id;
    el.dataset.username = msg.username;

    const usernameEl = node.querySelector('.chat-message-username');
    usernameEl.textContent = msg.username;
    if (msg.is_self) {
      el.classList.add('chat-message-self');
    }

    node.querySelector('.chat-message-time').textContent = formatTime(msg.created_at);

    // message content already escaped server-side; textContent here
    // is an extra safety layer, not a workaround for missing escaping.
    node.querySelector('.chat-message-text').textContent = msg.message;

    const reportBtn = node.querySelector('.chat-action-report');
    const blockBtn = node.querySelector('.chat-action-block');

    if (msg.is_self || !window.CURRENT_USERNAME) {
      // Can't report/block your own messages, and logged-out users
      // can't report/block at all.
      reportBtn.remove();
      blockBtn.remove();
    } else {
      reportBtn.addEventListener('click', () => reportMessage(msg.id, msg.username));
      blockBtn.addEventListener('click', () => blockUser(msg.username));
    }

    return node;
  }

  async function fetchMessages() {
    try {
      const res = await fetch('/api/chat/messages');
      if (!res.ok) throw new Error('Failed to load messages');
      const data = await res.json();

      if (chatLoadingEl) chatLoadingEl.remove();

      const wasScrolledToBottom =
        chatWindowEl.scrollHeight - chatWindowEl.scrollTop - chatWindowEl.clientHeight < 40;

      data.messages.forEach((msg) => {
        if (!knownMessageIds.has(msg.id)) {
          knownMessageIds.add(msg.id);
          chatMessagesEl.appendChild(renderMessage(msg));
        }
      });

      if (wasScrolledToBottom) {
        chatWindowEl.scrollTop = chatWindowEl.scrollHeight;
      }
    } catch (err) {
      console.error('Chat fetch error:', err);
    }
  }

  async function sendMessage(text) {
    const formData = new URLSearchParams();
    formData.append('message', text);

    const res = await fetch('/api/chat/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData.toString(),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Could not send message.');
    }

    // Immediately fetch so the sender sees their own message right away
    // instead of waiting for the next poll tick.
    await fetchMessages();
  }

  async function reportMessage(messageId, reportedUsername) {
    const reason = prompt(`Report a message from ${reportedUsername}? Optionally add a reason:`);
    if (reason === null) return; // cancelled

    const formData = new URLSearchParams();
    formData.append('message_id', messageId);
    if (reason) formData.append('reason', reason);

    try {
      const res = await fetch('/api/chat/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });
      if (!res.ok) throw new Error();
      alert('Thanks — this has been reported for review.');
    } catch {
      alert('Could not submit report. Please try again.');
    }
  }

  async function blockUser(username) {
    if (!confirm(`Block ${username}? You won't see their messages anymore.`)) return;

    const formData = new URLSearchParams();
    formData.append('blocked_username', username);

    try {
      const res = await fetch('/api/chat/block', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });
      if (!res.ok) throw new Error();

      // Remove that user's messages from view immediately.
      document
        .querySelectorAll(`.chat-message[data-username="${CSS.escape(username)}"]`)
        .forEach((el) => el.remove());
    } catch {
      alert('Could not block user. Please try again.');
    }
  }

  if (chatForm) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = chatInput.value.trim();
      if (!text) return;

      chatInput.disabled = true;
      try {
        await sendMessage(text);
        chatInput.value = '';
      } catch (err) {
        alert(err.message || 'Could not send message.');
      } finally {
        chatInput.disabled = false;
        chatInput.focus();
      }
    });
  }

  // Initial load + polling
  fetchMessages();
  pollTimer = setInterval(fetchMessages, POLL_INTERVAL_MS);

  // Pause polling when tab is hidden to be a little kinder to Render's
  // free tier / avoid waking a spun-down instance unnecessarily.
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      clearInterval(pollTimer);
    } else {
      fetchMessages();
      pollTimer = setInterval(fetchMessages, POLL_INTERVAL_MS);
    }
  });
})();
