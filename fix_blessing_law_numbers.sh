#!/data/data/com.termux/files/usr/bin/bash
# fix_blessing_law_numbers.sh — Fix Codex law numbers (16=Blessing, 17=Surplus)
# and clarify the Blessing payout is 10% of the pot, capped at $19k/$38k per year.
# Run from ~/the_commons

set -e

if [ ! -f "commons/blessing.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up files..."
cp commons/blessing.py commons/blessing.py.bak
cp commons/codex.py commons/codex.py.bak
cp templates/blessing.html templates/blessing.html.bak
cp templates/blessing_apply.html templates/blessing_apply.html.bak
cp templates/giving.html templates/giving.html.bak
echo "   Backed up: blessing.py, codex.py, blessing.html, blessing_apply.html, giving.html"

python3 << 'PYEOF'
def patch_file(path, replacements, label):
    with open(path, "r") as f:
        src = f.read()
    applied = 0
    for old, new in replacements:
        if old in src:
            src = src.replace(old, new, 1)
            applied += 1
        else:
            print(f"⚠️  [{label}] Could not find: {old[:60]}...")
    with open(path, "w") as f:
        f.write(src)
    print(f"✅ [{label}] {applied}/{len(replacements)} replacements applied.")

patch_file("commons/blessing.py", [
    ("Codex Law 18.", "Codex Law 16."),
], "commons/blessing.py")

patch_file("commons/codex.py", [
    (
        '"Maximum $19,000 for individuals, $38,000 for families "',
        '"Ten percent of the monthly community pot, up to a maximum of $19,000 "\n                "for individuals or $38,000 for families per calendar year "'
    ),
], "commons/codex.py")

patch_file("templates/blessing.html", [
    (
        '<p>Codex Law 18 — One person. One month. Community chosen.</p>',
        '<p>Codex Law 16 — One person. One month. Community chosen.</p>'
    ),
    (
        '<p>Maximum $19,000 for individuals. $38,000 for families. Every dollar transparent. The Commons is a facilitator only.</p>',
        '<p>Ten percent of the monthly community pot, up to a maximum of $19,000 for individuals or $38,000 for families per calendar year. Every dollar transparent. The Commons is a facilitator only.</p>'
    ),
], "templates/blessing.html")

patch_file("templates/blessing_apply.html", [
    (
        '<p>Medical. Housing. Food security. Genuine need only. Maximum $19,000 for individuals, $38,000 for families.</p>',
        '<p>Medical. Housing. Food security. Genuine need only. Ten percent of the monthly community pot, up to a maximum of $19,000 for individuals or $38,000 for families per calendar year.</p>'
    ),
], "templates/blessing_apply.html")

patch_file("templates/giving.html", [
    (
        '<p>Codex Laws 17 & 18 — Surplus to the World · The Monthly Blessing</p>',
        '<p>Codex Laws 16 & 17 — The Monthly Blessing · Surplus to the World</p>'
    ),
    (
        '<p>Maximum $19,000 for individuals. $38,000 for families. Every dollar transparent. The Commons is a facilitator only.</p>',
        '<p>Ten percent of the monthly community pot, up to a maximum of $19,000 for individuals or $38,000 for families per calendar year. Every dollar transparent. The Commons is a facilitator only.</p>'
    ),
], "templates/giving.html")

PYEOF

echo ""
echo "🎉 Done. Review the diffs with:"
echo "   diff commons/blessing.py.bak commons/blessing.py"
echo "   diff commons/codex.py.bak commons/codex.py"
echo "   diff templates/blessing.html.bak templates/blessing.html"
echo "   diff templates/blessing_apply.html.bak templates/blessing_apply.html"
echo "   diff templates/giving.html.bak templates/giving.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix Codex law numbers (16=Blessing, 17=Surplus) and clarify 10% pot rule'"
echo "   git push"
echo ""
echo "If something looks wrong, restore any file with:"
echo "   cp <file>.bak <file>"
