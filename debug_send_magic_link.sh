#!/data/data/com.termux/files/usr/bin/bash
# debug_send_magic_link.sh — Temporarily log full Resend API response for diagnosis
# This is a DIAGNOSTIC patch, not a permanent fix.
# Run from ~/the_commons

set -e

if [ ! -f "commons/email_auth.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up commons/email_auth.py..."
cp commons/email_auth.py commons/email_auth.py.bak2
echo "   -> commons/email_auth.py.bak2"

python3 << 'PYEOF'
path = "commons/email_auth.py"
with open(path, "r") as f:
    src = f.read()

old = '''def send_magic_link(email: str, token: str) -> bool:
    link = f"{config.base_url}/auth/magic?token={token}"
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {config.resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "The Commons <noreply@commonscommunity.org>",
                "to": [email],
                "subject": "Your sign-in link for The Commons",
                "text": f"""Hello,

Click the link below to sign in to The Commons.
This link expires in 24 hours.

{link}

If you didn't request this, ignore this email.

Power to the People.
— The Commons"""
            }
        )
        if response.status_code == 200:
            return True
        print(f"[EMAIL] Resend error: {response.text}")
        return False
    except Exception as e:
        print(f"[EMAIL] Failed to send: {e}")
        return False'''

new = '''def send_magic_link(email: str, token: str) -> bool:
    link = f"{config.base_url}/auth/magic?token={token}"
    print(f"[EMAIL DEBUG] Starting send to {email}")
    print(f"[EMAIL DEBUG] API key present: {bool(config.resend_api_key)}, length: {len(config.resend_api_key) if config.resend_api_key else 0}")
    print(f"[EMAIL DEBUG] API key prefix: {config.resend_api_key[:8] if config.resend_api_key else 'EMPTY'}...")
    try:
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {config.resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "The Commons <noreply@commonscommunity.org>",
                "to": [email],
                "subject": "Your sign-in link for The Commons",
                "text": f"""Hello,

Click the link below to sign in to The Commons.
This link expires in 24 hours.

{link}

If you didn't request this, ignore this email.

Power to the People.
— The Commons"""
            },
            timeout=15
        )
        print(f"[EMAIL DEBUG] Resend status code: {response.status_code}")
        print(f"[EMAIL DEBUG] Resend response body: {response.text}")
        if response.status_code == 200:
            return True
        print(f"[EMAIL] Resend error: {response.text}")
        return False
    except Exception as e:
        print(f"[EMAIL DEBUG] Exception type: {type(e).__name__}")
        print(f"[EMAIL] Failed to send: {e}")
        return False'''

if old not in src:
    print("❌ Could not find the send_magic_link function block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ commons/email_auth.py patched — will now log full Resend request/response details.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff commons/email_auth.py.bak2 commons/email_auth.py"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Temporary debug logging for Resend email sending'"
echo "   git push"
echo ""
echo "After we find the real bug, we'll REVERT this debug patch:"
echo "   cp commons/email_auth.py.bak2 commons/email_auth.py"
echo "   git add -A && git commit -m 'Remove debug logging'"
echo "   git push"
