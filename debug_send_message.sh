#!/data/data/com.termux/files/usr/bin/bash
# debug_send_message.sh — Temporarily show raw response when message send fails
# This is a DIAGNOSTIC patch, not a permanent fix — helps us see the real error.
# Run from ~/the_commons

set -e

if [ ! -f "templates/messages.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/messages.html..."
cp templates/messages.html templates/messages.html.bak4
echo "   -> templates/messages.html.bak4"

python3 << 'PYEOF'
path = "templates/messages.html"
with open(path, "r") as f:
    src = f.read()

old = '''      const res = await fetch('/api/messages/send', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token },
        body: form
      });
      const data = await res.json();
      if (data.ok) {
        status.style.color = 'var(--green-dark)';
        status.textContent = data.request ? 'Message request sent.' : 'Message sent.';
        document.getElementById('new-to').value = '';
        document.getElementById('new-content').value = '';
      } else {
        status.style.color = 'red';
        status.textContent = data.error || 'Could not send.';
      }
    }'''

new = '''      const res = await fetch('/api/messages/send', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + token },
        body: form
      });
      console.log('[DEBUG] Response status:', res.status);
      const rawText = await res.text();
      console.log('[DEBUG] Raw response body:', rawText);
      let data;
      try {
        data = JSON.parse(rawText);
      } catch (e) {
        status.style.color = 'red';
        status.textContent = 'DEBUG: Non-JSON response (status ' + res.status + '): ' + rawText.substring(0, 200);
        return;
      }
      if (data.ok) {
        status.style.color = 'var(--green-dark)';
        status.textContent = data.request ? 'Message request sent.' : 'Message sent.';
        document.getElementById('new-to').value = '';
        document.getElementById('new-content').value = '';
      } else {
        status.style.color = 'red';
        status.textContent = 'DEBUG (status ' + res.status + '): ' + JSON.stringify(data);
      }
    }'''

if old not in src:
    print("❌ Could not find the sendNewMessage fetch block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/messages.html patched — will now show raw error details for debugging.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/messages.html.bak4 templates/messages.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Temporary debug logging for message send failure'"
echo "   git push"
echo ""
echo "After we find the real bug, we'll REVERT this debug patch:"
echo "   cp templates/messages.html.bak4 templates/messages.html"
echo "   git add -A && git commit -m 'Remove debug logging'"
echo "   git push"
