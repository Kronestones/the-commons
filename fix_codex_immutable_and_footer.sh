#!/data/data/com.termux/files/usr/bin/bash
# fix_codex_immutable_and_footer.sh — Mark Laws 7 & 13 immutable (matching
# the others), rename "The Codex" to "Guidelines", and rewrite the closing text.
# Run from ~/the_commons

set -e

if [ ! -f "commons/codex.py" ] || [ ! -f "templates/codex.html" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up files..."
cp commons/codex.py commons/codex.py.bak2
cp templates/codex.html templates/codex.html.bak2
echo "   Backed up: commons/codex.py, templates/codex.html"

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

patch_file("commons/codex.py", [
    (
        '''            "number": 7,
            "name": "Dignity",
            "text": (
                "Every user has inherent dignity. "
                "Harassment, dehumanization, and targeted abuse "
                "are incompatible with this platform."
            ),
            "immutable": False,''',
        '''            "number": 7,
            "name": "Dignity",
            "text": (
                "Every user has inherent dignity. "
                "Harassment, dehumanization, and targeted abuse "
                "are incompatible with this platform."
            ),
            "immutable": True,'''
    ),
    (
        '''            "number": 13,
            "name": "Wellbeing",
            "text": (
                "The platform cares about the people who use it. "
                "Session nudges, content pattern awareness, youth protections — "
                "these are not restrictions. They are care."
            ),
            "immutable": False,''',
        '''            "number": 13,
            "name": "Wellbeing",
            "text": (
                "The platform cares about the people who use it. "
                "Session nudges, content pattern awareness, youth protections — "
                "these are not restrictions. They are care."
            ),
            "immutable": True,'''
    ),
], "commons/codex.py")

patch_file("templates/codex.html", [
    (
        '<h1 class="codex-title">The Codex</h1>',
        '<h1 class="codex-title">Guidelines</h1>'
    ),
    (
        '''    <p style="font-size:14px;margin-bottom:8px;">The Codex is the architecture of The Commons — the design, the programming, the foundation.</p>''',
        '''    <p style="font-size:14px;margin-bottom:8px;">Guidelines are the programming design of The Commons. They are permanent and can't be changed.</p>'''
    ),
    (
        '''    <p style="font-size:14px;margin-bottom:12px;">It is permanent. And it is our promise to every person who joins this community.</p>''',
        '''    <p style="font-size:14px;margin-bottom:12px;">And it is our promise to every person who joins this community.</p>'''
    ),
    (
        '''    <p style="font-size:11px;color:var(--muted);margin-top:10px;opacity:0.7;">We reserve the right to remove users who violate the Codex.</p>''',
        '''    <p style="font-size:11px;color:var(--muted);margin-top:10px;opacity:0.7;">We reserve the right to remove users who violate guidelines.</p>'''
    ),
], "templates/codex.html")

PYEOF

echo ""
echo "🎉 Done. Review the diffs with:"
echo "   diff commons/codex.py.bak2 commons/codex.py"
echo "   diff templates/codex.html.bak2 templates/codex.html"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Mark Laws 7 & 13 immutable, rename Codex to Guidelines, rewrite closing text'"
echo "   git push"
echo ""
echo "If something looks wrong, restore any file with:"
echo "   cp <file>.bak2 <file>"
