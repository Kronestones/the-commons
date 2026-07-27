#!/data/data/com.termux/files/usr/bin/bash
# fix_market_inbox.sh — Add Marketplace tab to messages.html
# Splits inbox into "Inbox" (regular) and "Market" (🛍️ prefixed) conversations
# No backend/schema changes needed — filters on existing last_message field
# Run from ~/the_commons

set -e

if [ ! -f "templates/messages.html" ]; then
    echo "❌ Run this from the_commons project root (templates/messages.html not found here)."
    exit 1
fi

echo "📦 Backing up templates/messages.html..."
cp templates/messages.html templates/messages.html.bak
echo "   -> templates/messages.html.bak"

python3 << 'PYEOF'
path = "templates/messages.html"
with open(path, "r") as f:
    src = f.read()

# ── 1. Add Market tab button ──────────────────────────────────────────────
old_tabs = '''    <div style="display:flex;gap:8px;margin-bottom:16px;">
      <button onclick="showTab('inbox')" id="tab-inbox" class="vote-btn">Inbox</button>
      <button onclick="showTab('requests')" id="tab-requests" class="vote-btn">Requests <span id="req-count"></span></button>
      <button onclick="showTab('new')" id="tab-new" class="vote-btn">+ New</button>
    </div>'''

new_tabs = '''    <div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
      <button onclick="showTab('inbox')" id="tab-inbox" class="vote-btn">Inbox</button>
      <button onclick="showTab('market')" id="tab-market" class="vote-btn">🛍️ Market</button>
      <button onclick="showTab('requests')" id="tab-requests" class="vote-btn">Requests <span id="req-count"></span></button>
      <button onclick="showTab('new')" id="tab-new" class="vote-btn">+ New</button>
    </div>'''

if old_tabs not in src:
    print("❌ Could not find the tabs block. Aborting — no changes made.")
    raise SystemExit(1)
src = src.replace(old_tabs, new_tabs, 1)

old_pane = '''    <!-- Inbox -->
    <div id="pane-inbox"></div>'''

new_pane = '''    <!-- Inbox -->
    <div id="pane-inbox"></div>

    <!-- Market -->
    <div id="pane-market" style="display:none"></div>'''

if old_pane not in src:
    print("❌ Could not find the inbox pane div. Aborting — no changes made.")
    raise SystemExit(1)
src = src.replace(old_pane, new_pane, 1)

old_showtab = '''    function showTab(tab) {
      ['inbox','requests','new','conversation'].forEach(t => {
        document.getElementById('pane-' + t).style.display = 'none';
        const btn = document.getElementById('tab-' + t);
        if (btn) btn.style.opacity = '0.6';
      });
      document.getElementById('pane-' + tab).style.display = 'block';
      const btn = document.getElementById('tab-' + tab);
      if (btn) btn.style.opacity = '1';
      if (tab === 'inbox') loadInbox();
      if (tab === 'requests') loadRequests();
    }'''

new_showtab = '''    function showTab(tab) {
      ['inbox','market','requests','new','conversation'].forEach(t => {
        document.getElementById('pane-' + t).style.display = 'none';
        const btn = document.getElementById('tab-' + t);
        if (btn) btn.style.opacity = '0.6';
      });
      document.getElementById('pane-' + tab).style.display = 'block';
      const btn = document.getElementById('tab-' + tab);
      if (btn) btn.style.opacity = '1';
      if (tab === 'inbox') loadInbox();
      if (tab === 'market') loadMarket();
      if (tab === 'requests') loadRequests();
    }

    function isMarketMessage(m) {
      return (m.last_message || '').startsWith('🛍️');
    }'''

if old_showtab not in src:
    print("❌ Could not find the showTab() function. Aborting — no changes made.")
    raise SystemExit(1)
src = src.replace(old_showtab, new_showtab, 1)

old_loadinbox = '''    async function loadInbox() {
      const res = await fetch('/api/messages/inbox', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      const data = await res.json();
      const pane = document.getElementById('pane-inbox');
      if (!data.inbox || data.inbox.length === 0) {
        pane.innerHTML = '<p style="color:var(--muted);text-align:center;padding:32px;">No messages yet.</p>';
        return;
      }
      pane.innerHTML = data.inbox.map(m => `
        <div class="post-card" onclick="openConvo('${m.username}')" style="cursor:pointer;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <strong>@${m.username}</strong>
            <span style="font-size:12px;color:var(--muted);">${formatTime(m.time)}</span>
          </div>
          <p style="margin:4px 0 0;color:var(--muted);font-size:14px;">${m.last_message.substring(0,80)}${m.last_message.length>80?'...':''}</p>
          ${m.unread ? '<span style="color:var(--green-dark);font-size:12px;font-weight:600;">● New</span>' : ''}
        </div>
      `).join('');
    }'''

new_loadinbox = '''    async function loadInbox() {
      const res = await fetch('/api/messages/inbox', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      const data = await res.json();
      const pane = document.getElementById('pane-inbox');
      const regular = (data.inbox || []).filter(m => !isMarketMessage(m));
      if (regular.length === 0) {
        pane.innerHTML = '<p style="color:var(--muted);text-align:center;padding:32px;">No messages yet.</p>';
        return;
      }
      pane.innerHTML = regular.map(m => `
        <div class="post-card" onclick="openConvo('${m.username}')" style="cursor:pointer;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <strong>@${m.username}</strong>
            <span style="font-size:12px;color:var(--muted);">${formatTime(m.time)}</span>
          </div>
          <p style="margin:4px 0 0;color:var(--muted);font-size:14px;">${m.last_message.substring(0,80)}${m.last_message.length>80?'...':''}</p>
          ${m.unread ? '<span style="color:var(--green-dark);font-size:12px;font-weight:600;">● New</span>' : ''}
        </div>
      `).join('');
    }

    async function loadMarket() {
      const res = await fetch('/api/messages/inbox', {
        headers: { 'Authorization': 'Bearer ' + token }
      });
      const data = await res.json();
      const pane = document.getElementById('pane-market');
      const market = (data.inbox || []).filter(m => isMarketMessage(m));
      if (market.length === 0) {
        pane.innerHTML = '<p style="color:var(--muted);text-align:center;padding:32px;">No marketplace messages yet.</p>';
        return;
      }
      pane.innerHTML = market.map(m => `
        <div class="post-card" onclick="openConvo('${m.username}')" style="cursor:pointer;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <strong>🛍️ @${m.username}</strong>
            <span style="font-size:12px;color:var(--muted);">${formatTime(m.time)}</span>
          </div>
          <p style="margin:4px 0 0;color:var(--muted);font-size:14px;">${m.last_message.substring(0,80)}${m.last_message.length>80?'...':''}</p>
          ${m.unread ? '<span style="color:var(--green-dark);font-size:12px;font-weight:600;">● New</span>' : ''}
        </div>
      `).join('');
    }'''

if old_loadinbox not in src:
    print("❌ Could not find the loadInbox() function. Aborting — no changes made.")
    raise SystemExit(1)
src = src.replace(old_loadinbox, new_loadinbox, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/messages.html patched — Market tab added, no backend changes needed.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/messages.html.bak templates/messages.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Add Marketplace tab to inbox'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/messages.html.bak templates/messages.html"
