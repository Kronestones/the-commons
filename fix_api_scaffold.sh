#!/data/data/com.termux/files/usr/bin/bash
# fix_api_scaffold.sh — Scaffold Anthropic API integration
# Adds anthropic_api_key config slot + api_response() stub in team_messaging.py
# Falls back to existing rule-based responses when no key is set — nothing breaks today.
# Run from ~/the_commons

set -e

if [ ! -f "commons/config.py" ] || [ ! -f "commons/team_messaging.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up files..."
cp commons/config.py commons/config.py.bak
cp commons/team_messaging.py commons/team_messaging.py.bak
echo "   -> commons/config.py.bak"
echo "   -> commons/team_messaging.py.bak"

# ── Patch commons/config.py: add anthropic_api_key slot ───────────────────
python3 << 'PYEOF'
path = "commons/config.py"
with open(path, "r") as f:
    src = f.read()

old = '''        self.resend_api_key      = os.getenv("RESEND_API_KEY", "")'''

new = '''        self.resend_api_key      = os.getenv("RESEND_API_KEY", "")
        self.anthropic_api_key   = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_model     = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")'''

if old not in src:
    print("❌ Could not find the resend_api_key line in config.py. Aborting.")
    raise SystemExit(1)
src = src.replace(old, new, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ commons/config.py patched — anthropic_api_key and anthropic_model slots added.")
PYEOF

# ── Patch commons/team_messaging.py: add api_response() with fallback ─────
python3 << 'PYEOF'
path = "commons/team_messaging.py"
with open(path, "r") as f:
    src = f.read()

old_imports = '''from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Session
from .database import Base
from .circle_assistants import ALL_PROFILES, ALL_TEAMS'''

new_imports = '''from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Session
from .database import Base
from .circle_assistants import ALL_PROFILES, ALL_TEAMS
from .config import config'''

if old_imports not in src:
    print("❌ Could not find the imports block in team_messaging.py. Aborting.")
    raise SystemExit(1)
src = src.replace(old_imports, new_imports, 1)

old_get_response = '''def get_member_response(member: str, message: str) -> str:
    """Generate a rule-based response from a team member."""
    member = member.lower()
    if member not in ALL_PROFILES:
        return "I don't recognise that team member."'''

new_get_response = '''def api_response(member: str, message: str, history: list = None) -> Optional[str]:
    """
    Generate a real response from a team member using the Anthropic API.
    Returns None if no API key is configured, or if the call fails —
    callers should fall back to get_member_response() in that case.

    To activate: set ANTHROPIC_API_KEY in Render's environment variables.
    Optionally set ANTHROPIC_MODEL (defaults to claude-haiku-4-5-20251001).
    """
    if not config.anthropic_api_key:
        return None

    member = member.lower()
    if member not in ALL_PROFILES:
        return None

    profile = ALL_PROFILES[member]

    system_prompt = (
        f"You are {profile['name']}, known as \\"{profile['quality']}\\" on The Commons "
        f"platform's moderation team. {profile['description']} "
        f"You are speaking directly with the Sovereign (the platform's founder). "
        f"Respond in character, briefly and naturally — a few sentences, not a report. "
        f"Do not break character or mention that you are an AI assistant."
    )

    try:
        import requests
        payload_messages = []
        if history:
            for h in history:
                role = "assistant" if h.get("direction") == "from" else "user"
                payload_messages.append({"role": role, "content": h.get("content", "")})
        payload_messages.append({"role": "user", "content": message})

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": config.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": config.anthropic_model,
                "max_tokens": 400,
                "system": system_prompt,
                "messages": payload_messages,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        return text.strip() or None
    except Exception as e:
        print(f"[TEAM_MESSAGING] api_response error for {member}: {e}")
        return None


def get_member_response(member: str, message: str) -> str:
    """Generate a rule-based response from a team member."""
    member = member.lower()
    if member not in ALL_PROFILES:
        return "I don't recognise that team member."'''

if old_get_response not in src:
    print("❌ Could not find get_member_response() in team_messaging.py. Aborting.")
    raise SystemExit(1)
src = src.replace(old_get_response, new_get_response, 1)

# Add Optional import for the type hint used above
old_typing_check = "from datetime import datetime\nfrom sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey\nfrom sqlalchemy.orm import Session\nfrom .database import Base\nfrom .circle_assistants import ALL_PROFILES, ALL_TEAMS\nfrom .config import config"
new_typing_check = "from datetime import datetime\nfrom typing import Optional\nfrom sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey\nfrom sqlalchemy.orm import Session\nfrom .database import Base\nfrom .circle_assistants import ALL_PROFILES, ALL_TEAMS\nfrom .config import config"

if old_typing_check not in src:
    print("❌ Could not find the import block to add typing.Optional. Aborting.")
    raise SystemExit(1)
src = src.replace(old_typing_check, new_typing_check, 1)

# Wire send_sovereign_message() to try api_response() first, fall back to rule-based
old_send = '''def send_sovereign_message(db: Session, member: str, content: str) -> dict:
    """Store a sovereign message and generate team response."""
    if member.lower() not in ALL_PROFILES:
        return {"ok": False, "error": f"No team member named {member}."}

    # Store sovereign's message
    db.add(SovereignMessage(
        member    = member.lower(),
        direction = "to",
        content   = content
    ))

    # Generate and store response
    response = get_member_response(member, content)
    db.add(SovereignMessage(
        member    = member.lower(),
        direction = "from",
        content   = response
    ))
    db.commit()

    return {"ok": True, "response": response}'''

new_send = '''def send_sovereign_message(db: Session, member: str, content: str) -> dict:
    """Store a sovereign message and generate team response.

    Tries the real Anthropic API first (if ANTHROPIC_API_KEY is set in
    Render's environment). Falls back to the rule-based response if no
    key is configured or the API call fails for any reason.
    """
    if member.lower() not in ALL_PROFILES:
        return {"ok": False, "error": f"No team member named {member}."}

    # Store sovereign's message
    db.add(SovereignMessage(
        member    = member.lower(),
        direction = "to",
        content   = content
    ))

    # Pull recent history for conversational context (used only if API is active)
    history = get_conversation(db, member)

    # Try real API response first; fall back to rule-based if unavailable
    response = api_response(member, content, history)
    if response is None:
        response = get_member_response(member, content)

    db.add(SovereignMessage(
        member    = member.lower(),
        direction = "from",
        content   = response
    ))
    db.commit()

    return {"ok": True, "response": response}'''

if old_send not in src:
    print("❌ Could not find send_sovereign_message() in team_messaging.py. Aborting.")
    raise SystemExit(1)
src = src.replace(old_send, new_send, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ commons/team_messaging.py patched — api_response() added with safe fallback.")
PYEOF

echo ""
echo "🎉 Done. Review the diffs with:"
echo "   diff commons/config.py.bak commons/config.py"
echo "   diff commons/team_messaging.py.bak commons/team_messaging.py"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Scaffold Anthropic API integration for team chat (inactive until key is set)'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp commons/config.py.bak commons/config.py"
echo "   cp commons/team_messaging.py.bak commons/team_messaging.py"
echo ""
echo "NOTE: This makes NO functional change to your live site right now."
echo "It only activates once you add ANTHROPIC_API_KEY to Render's environment variables."
