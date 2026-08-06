#!/data/data/com.termux/files/usr/bin/bash
# fix_giving_trim.sh — Trim repetitive text from the giving page and
# update "Architect Founder Krone" naming to match the guidelines page fix.
# Run from ~/the_commons

set -e

if [ ! -f "templates/giving.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/giving.html..."
cp templates/giving.html templates/giving.html.bak2
echo "   -> templates/giving.html.bak2"

python3 << 'PYEOF'
path = "templates/giving.html"
with open(path, "r") as f:
    src = f.read()

replacements = [
    (
        '    <p>Codex Laws 16 & 17 — The Monthly Blessing · Surplus to the World</p>\n',
        ''
    ),
    (
        '    <p>One person. One month. Community chosen.</p>\n',
        ''
    ),
    (
        '<p>Medical. Housing. Food security. Genuine life-sustaining need only. Not wants.</p>',
        '<p>Medical. Housing. Food security. Genuine life-sustaining need only.</p>'
    ),
    (
        '<p>Ten percent of the monthly community pot, up to a maximum of $19,000 for individuals or $38,000 for families per calendar year. Every dollar transparent. The Commons is a facilitator only.</p>',
        '<p>Ten percent of the monthly community pot, up to a maximum of $19,000 for individuals or $38,000 for families per calendar year. Every dollar transparent.</p>'
    ),
    (
        '<p>Any money remaining after operating costs are covered is donated to a humanitarian cause every six months. Not kept. Not invested for profit. Given.</p>',
        '<p>Any money remaining after operating costs are covered is donated to a humanitarian cause. Not kept. Not invested for profit. Given.</p>'
    ),
    (
        'Architect Founder Krone designates the cause. Every donation is published here.',
        'The Founder of The Commons designates the cause. Every donation is published here.'
    ),
    (
        '<p>Every dollar collected in platform fees is accounted for here. Operating costs are published monthly. Any surplus goes to humanitarian causes every six months.</p>',
        '<p>Every dollar collected in platform fees is accounted for here. Operating costs are published monthly. Any surplus goes to humanitarian causes.</p>'
    ),
]

applied = 0
for old, new in replacements:
    if old in src:
        src = src.replace(old, new, 1)
        applied += 1
    else:
        print(f"⚠️  Could not find: {old[:70]}...")

with open(path, "w") as f:
    f.write(src)

print(f"✅ templates/giving.html patched — {applied}/{len(replacements)} replacements applied.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/giving.html.bak2 templates/giving.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Trim repetitive text on giving page, update naming'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/giving.html.bak2 templates/giving.html"
