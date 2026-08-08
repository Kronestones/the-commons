#!/data/data/com.termux/files/usr/bin/bash
# fix_codex_footer_and_surplus.sh — Remove duplicate footer line and
# Owner/Founder signature, and update the marketplace paragraph's
# closing sentence to describe where surplus actually goes.
# Run from ~/the_commons

set -e

if [ ! -f "templates/codex.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up templates/codex.html..."
cp templates/codex.html templates/codex.html.bak3
echo "   -> templates/codex.html.bak3"

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
            print(f"⚠️  [{label}] Could not find: {old[:70]}...")
    with open(path, "w") as f:
        f.write(src)
    print(f"✅ [{label}] {applied}/{len(replacements)} replacements applied.")

patch_file("templates/codex.html", [
    (
        '''    <p style="font-size:14px;margin-bottom:8px;">Guidelines are the programming design of The Commons. They are permanent and can't be changed.</p>
    <p style="font-size:14px;margin-bottom:8px;">It cannot be changed.</p>
    <p style="font-size:14px;margin-bottom:12px;">And it is our promise to every person who joins this community.</p>
    <p class="codex-footer-sig" style="font-size:14px;">— {{ codex.SOVEREIGN }}</p>
    <p class="codex-footer-spirit" style="font-size:15px;">Power to the People. 🏡</p>''',
        '''    <p style="font-size:14px;margin-bottom:8px;">Guidelines are the programming design of The Commons. They are permanent and can't be changed.</p>
    <p style="font-size:14px;margin-bottom:12px;">And it is our promise to every person who joins this community.</p>
    <p class="codex-footer-spirit" style="font-size:15px;">Power to the People. 🏡</p>'''
    ),
    (
        '<p>Local small businesses and individual creators can sell their products through it. The platform takes a flat $1 per sale — just enough to keep the lights on. Any surplus goes back into the platform. No profit. Ever.</p>',
        '<p>Local small businesses and individual creators can sell their products through it. The platform takes a flat $1 per sale — just enough to keep the lights on. Any surplus after operating costs is donated to the Monthly Blessing or the bi-annual humanitarian donation. No profit. Ever.</p>'
    ),
], "templates/codex.html")

PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff templates/codex.html.bak3 templates/codex.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Clean up guidelines footer, update surplus destination in marketplace paragraph'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp templates/codex.html.bak3 templates/codex.html"
