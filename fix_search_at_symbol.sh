#!/data/data/com.termux/files/usr/bin/bash
# fix_search_at_symbol.sh — Strip leading @ from search queries so @username searches work
# Run from ~/the_commons

set -e

if [ ! -f "templates/index.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/index.html..."
cp templates/index.html templates/index.html.bak
echo "   -> templates/index.html.bak"

python3 << 'PYEOF'
path = "templates/index.html"
with open(path, "r") as f:
    src = f.read()

old = '''function runSearch(q) {
  clearTimeout(searchTimer);
  const results = document.getElementById('search-results');
  const clear   = document.getElementById('search-clear');
  if (!q || q.length < 2) {
    results.style.display = 'none';
    clear.style.display = 'none';
    return;
  }
  clear.style.display = 'block';
  searchTimer = setTimeout(async () => {
    const token = localStorage.getItem('token');
    const res = await fetch('/api/search?q=' + encodeURIComponent(q) + '&type=all', {
      headers: { 'Authorization': 'Bearer ' + token }
    });'''

new = '''function runSearch(q) {
  clearTimeout(searchTimer);
  const results = document.getElementById('search-results');
  const clear   = document.getElementById('search-clear');
  // Strip a leading @ so "@username" and "username" both search correctly —
  // stored usernames in the database never include the @ symbol.
  const cleanQ = q.replace(/^@+/, '');
  if (!cleanQ || cleanQ.length < 2) {
    results.style.display = 'none';
    clear.style.display = 'none';
    return;
  }
  clear.style.display = 'block';
  searchTimer = setTimeout(async () => {
    const token = localStorage.getItem('token');
    const res = await fetch('/api/search?q=' + encodeURIComponent(cleanQ) + '&type=all', {
      headers: { 'Authorization': 'Bearer ' + token }
    });'''

if old not in src:
    print("❌ Could not find the runSearch() function. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ templates/index.html patched — leading @ now stripped before searching.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/index.html.bak templates/index.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix search: strip leading @ symbol so username search works'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/index.html.bak templates/index.html"
