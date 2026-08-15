#!/data/data/com.termux/files/usr/bin/bash
# add_engineering_panel.sh — Add a test panel to the Sovereign Dashboard
# for consulting Team Keel and Team Ballast on real problems.
# Run from ~/the_commons

set -e

if [ ! -f "templates/sovereign.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/sovereign.html..."
cp templates/sovereign.html templates/sovereign.html.bak4
echo "   -> templates/sovereign.html.bak4"

python3 << 'PYEOF'
path = "templates/sovereign.html"
with open(path, "r") as f:
    src = f.read()

old = '''    <textarea id="team-message" placeholder="Write your message..." style="width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;font-size:15px;min-height:100px;resize:vertical;"></textarea>
    <button onclick="sendTeamMessage()" class="vote-btn" style="width:100%;margin-top:8px;">Send Message</button>
    <div id="team-msg-status" style="margin-top:8px;"></div>
  </div>
'''

new = '''    <textarea id="team-message" placeholder="Write your message..." style="width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;font-size:15px;min-height:100px;resize:vertical;"></textarea>
    <button onclick="sendTeamMessage()" class="vote-btn" style="width:100%;margin-top:8px;">Send Message</button>
    <div id="team-msg-status" style="margin-top:8px;"></div>
  </div>

  <!-- Engineering Consultation -->
  <div class="post-card" style="margin-bottom:16px;">
    <h2 style="margin-bottom:12px;">Consult Engineering Teams</h2>
    <p style="font-size:13px;color:var(--muted);margin-bottom:12px;">Describe a real problem — Team Keel, Team Ballast, or both will give their diagnosis.</p>
    <select id="eng-team-select" style="width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;margin-bottom:8px;font-size:15px;">
      <option value="keel">Team Keel</option>
      <option value="ballast">Team Ballast</option>
      <option value="both">Both Teams</option>
    </select>
    <textarea id="eng-problem" placeholder="Describe the problem..." style="width:100%;padding:10px;border:1px solid var(--border);border-radius:8px;font-size:15px;min-height:80px;resize:vertical;"></textarea>
    <button onclick="consultEngineering()" class="vote-btn" style="width:100%;margin-top:8px;">Consult</button>
    <div id="eng-status" style="margin-top:8px;"></div>
    <div id="eng-results" style="margin-top:12px;"></div>
  </div>
'''

if old not in src:
    print("❌ Could not find the Message a Team block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

old_js_anchor = "async function sendTeamMessage() {"
new_js = '''async function consultEngineering() {
  const teamSelect = document.getElementById('eng-team-select').value;
  const problem = document.getElementById('eng-problem').value.trim();
  const status = document.getElementById('eng-status');
  const results = document.getElementById('eng-results');
  if (!problem) { status.textContent = 'Please describe the problem.'; return; }

  status.textContent = 'Consulting...';
  results.innerHTML = '';

  const form = new FormData();
  form.append('problem', problem);

  const endpoint = teamSelect === 'both'
    ? '/api/engineering/consult-both'
    : '/api/engineering/consult/' + teamSelect;

  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + token },
    body: form
  });
  const data = await res.json();

  if (!data.ok) {
    status.textContent = data.error || 'Could not consult team.';
    return;
  }
  status.textContent = 'Done.';

  function renderTeamResult(teamResult) {
    if (!teamResult.ok) return '<p style="color:red;">' + teamResult.error + '</p>';
    let html = '<h3 style="margin:12px 0 8px;">' + teamResult.team + '</h3>';
    teamResult.analyses.forEach(a => {
      html += '<div style="padding:8px;border-bottom:1px solid var(--border);">' +
        '<strong>' + a.member + '</strong>' +
        '<p style="font-size:13px;color:var(--muted);margin:4px 0;">' + a.code_gift + '</p>' +
        '<p style="font-size:14px;">' + a.diagnosis + '</p>' +
        '</div>';
    });
    html += '<div style="padding:8px;background:var(--bg);border-radius:8px;margin-top:8px;">' +
      '<strong>' + teamResult.lead_synthesis.member + ' (Lead Synthesis)</strong>' +
      '<p style="font-size:14px;">' + teamResult.lead_synthesis.diagnosis + '</p>' +
      '</div>';
    return html;
  }

  if (teamSelect === 'both') {
    results.innerHTML = renderTeamResult(data.keel) + renderTeamResult(data.ballast);
  } else {
    results.innerHTML = renderTeamResult(data);
  }
}

async function sendTeamMessage() {'''

if old_js_anchor not in src:
    print("❌ Could not find sendTeamMessage() function. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old_js_anchor, new_js, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/sovereign.html patched — Engineering Consultation panel added.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/sovereign.html.bak4 templates/sovereign.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Add engineering consultation test panel to Sovereign Dashboard'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/sovereign.html.bak4 templates/sovereign.html"
