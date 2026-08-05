#!/data/data/com.termux/files/usr/bin/bash
# fix_codex_trim.sh — Trim repetitive text from the guidelines page and
# update "Architect Founder Krone" naming across the site.
# Run from ~/the_commons

set -e

if [ ! -f "templates/codex.html" ] || [ ! -f "commons/codex.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up files..."
cp templates/codex.html templates/codex.html.bak
cp commons/codex.py commons/codex.py.bak
echo "   Backed up: templates/codex.html, commons/codex.py"

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
        '<p>Local small businesses and individual creators can sell their products through it. The platform takes a flat $1 per sale — not a percentage, not advertising revenue, just enough to keep the lights on. Any surplus goes back into the platform. No profit. Ever.</p>',
        '<p>Local small businesses and individual creators can sell their products through it. The platform takes a flat $1 per sale — just enough to keep the lights on. Any surplus goes back into the platform. No profit. Ever.</p>'
    ),
    (
        '    <p>Any surplus above operating costs is directed to humanitarian causes every 6 months and to The Monthly Blessing — community chosen, community voted. Every dollar is transparent and publicly available on the platform.</p>\n',
        ''
    ),
    (
        '    <p class="codex-laws-intro">These guidelines govern The Commons. No guideline can be quietly changed. Every amendment is logged publicly.</p>\n',
        ''
    ),
    (
        '<p style="font-size:14px;margin-bottom:8px;">It cannot be changed. It cannot be quietly updated. It cannot be overridden by business interests.</p>',
        '<p style="font-size:14px;margin-bottom:8px;">It cannot be changed.</p>'
    ),
], "templates/codex.html")

patch_file("commons/codex.py", [
    (
        "— Architect Founder Krone · The Commons · 2026",
        "— The Owner and Founder · The Commons · 2026"
    ),
    (
        'SOVEREIGN = "Architect Founder Krone"',
        'SOVEREIGN = "the Owner and Founder"'
    ),
    (
        '                "Ten percent of monthly surplus is set aside for this purpose. "\n'
        '                "The team verifies need — medical, housing, food security. "\n'
        '                "Not wants. The community votes. The highest vote wins. "\n'
        '                "One blessing. One person or family. Every month. "\n'
        '                "Ten percent of the monthly community pot, up to a maximum of $19,000 "\n'
        '                "for individuals or $38,000 for families per calendar year "\n'
        '                "per calendar year. Every application, every vote, "\n'
        '                "every dollar is published publicly. "\n'
        '                "The Commons is a facilitator only. "\n'
        '                "This is the community caring for its own."',
        '                "Ten percent of monthly surplus is set aside for this purpose. "\n'
        '                "The team verifies need — medical, housing, food security. "\n'
        '                "The community votes. The highest vote wins. "\n'
        '                "One blessing. One person or family. Every month. "\n'
        '                "Ten percent of the monthly community pot, up to a maximum of $19,000 "\n'
        '                "for individuals or $38,000 for families per calendar year. "\n'
        '                "Every application, every vote, "\n'
        '                "every dollar is published publicly. "\n'
        '                "This is the community caring for its own."'
    ),
    (
        '                "Architect Founder Krone designates the cause. "',
        '                "The Founder of The Commons designates the cause. "'
    ),
], "commons/codex.py")

PYEOF

echo ""
echo "🎉 Done. Review the diffs with:"
echo "   diff templates/codex.html.bak templates/codex.html"
echo "   diff commons/codex.py.bak commons/codex.py"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Trim repetitive Codex text, fix duplicated per-calendar-year, update naming'"
echo "   git push"
echo ""
echo "If something looks wrong, restore any file with:"
echo "   cp <file>.bak <file>"
