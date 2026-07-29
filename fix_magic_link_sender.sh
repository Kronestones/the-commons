#!/data/data/com.termux/files/usr/bin/bash
# fix_magic_link_sender.sh — Send magic link emails from verified commonscommunity.org
# domain instead of Resend's restricted onboarding@resend.dev sandbox address.
# Run from ~/the_commons

set -e

if [ ! -f "commons/email_auth.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up commons/email_auth.py..."
cp commons/email_auth.py commons/email_auth.py.bak
echo "   -> commons/email_auth.py.bak"

python3 << 'PYEOF'
path = "commons/email_auth.py"
with open(path, "r") as f:
    src = f.read()

old = '''                "from": "The Commons <onboarding@resend.dev>",'''

new = '''                "from": "The Commons <noreply@commonscommunity.org>",'''

if old not in src:
    print("❌ Could not find the sandbox sender line. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ commons/email_auth.py patched — now sends from noreply@commonscommunity.org")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff commons/email_auth.py.bak commons/email_auth.py"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix magic link emails: send from verified domain instead of Resend sandbox'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp commons/email_auth.py.bak commons/email_auth.py"
