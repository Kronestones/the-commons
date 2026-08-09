#!/data/data/com.termux/files/usr/bin/bash
# install_engineering_teams.sh — Install commons/engineering_teams.py
# (Team Keel & Team Ballast) and wire it into main.py's startup + routes.
#
# IMPORTANT: Before running this, move the downloaded engineering_teams.py
# into commons/ manually:
#   mv ~/storage/downloads/engineering_teams.py ~/the_commons/commons/
#
# Run from ~/the_commons

set -e

if [ ! -f "commons/engineering_teams.py" ]; then
    echo "❌ commons/engineering_teams.py not found."
    echo "   Move it there first: mv ~/storage/downloads/engineering_teams.py ~/the_commons/commons/"
    exit 1
fi

if [ ! -f "main.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up main.py..."
cp main.py main.py.bak7
echo "   -> main.py.bak7"

python3 << 'PYEOF'
path = "main.py"
with open(path, "r") as f:
    src = f.read()

old_import = "from commons.circle_assistants import circle_assistants, AssistantAnalysis"
new_import = (
    "from commons.circle_assistants import circle_assistants, AssistantAnalysis\n"
    "from commons.engineering_teams   import engineering_consultation, EngineeringConsultation, ENGINEERING_TEAMS"
)
if old_import not in src:
    print("❌ Could not find the circle_assistants import line. Aborting.")
    raise SystemExit(1)
src = src.replace(old_import, new_import, 1)

old_startup = "    from commons.circle_assistants import AssistantAnalysis"
new_startup = (
    "    from commons.circle_assistants import AssistantAnalysis\n"
    "    from commons.engineering_teams import EngineeringConsultation"
)
if old_startup not in src:
    print("❌ Could not find the AssistantAnalysis startup import. Aborting.")
    raise SystemExit(1)
src = src.replace(old_startup, new_startup, 1)

old_anchor = "# ── Translation API ───────────────────────────────────────────────────────"
new_routes = '''# ── Engineering Teams API (Keel & Ballast) ────────────────────────────────────

@app.get("/api/engineering/teams")
async def api_engineering_teams(
    current_user: User = Depends(get_current_user),
):
    """List Team Keel and Team Ballast."""
    if current_user.role.value not in ("circle", "sovereign"):
        raise HTTPException(403, "Circle or Sovereign access required.")
    return JSONResponse({"ok": True, "teams": ENGINEERING_TEAMS})

@app.post("/api/engineering/consult/{team_key}")
async def api_engineering_consult(
    team_key:     str,
    problem:      str = Form(...),
    code_context: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Consult one engineering team (keel or ballast) on a real problem."""
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign access required.")
    result = engineering_consultation.consult_team(db, team_key, problem, code_context)
    return JSONResponse(result)

@app.post("/api/engineering/consult-both")
async def api_engineering_consult_both(
    problem:      str = Form(...),
    code_context: str = Form(default=""),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Consult BOTH Team Keel and Team Ballast together on a real problem."""
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign access required.")
    result = engineering_consultation.consult_both_teams(db, problem, code_context)
    return JSONResponse(result)

@app.get("/api/engineering/pending")
async def api_engineering_pending(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get pending (unreviewed) engineering consultations."""
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign access required.")
    return JSONResponse({"ok": True, "pending": engineering_consultation.get_pending(db)})

@app.post("/api/engineering/reviewed/{consultation_id}")
async def api_engineering_reviewed(
    consultation_id: int,
    current_user:    User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark an engineering consultation as reviewed."""
    if current_user.role.value != "sovereign":
        raise HTTPException(403, "Sovereign access required.")
    return JSONResponse(engineering_consultation.mark_reviewed(db, consultation_id))


# ── Translation API ───────────────────────────────────────────────────────────'''

if old_anchor not in src:
    print("❌ Could not find the Translation API anchor comment. Aborting.")
    raise SystemExit(1)
src = src.replace(old_anchor, new_routes, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ main.py patched — engineering_teams imported, table registered, 5 new API routes added.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff main.py.bak7 main.py"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Install Team Keel and Team Ballast engineering teams'"
echo "   git push"
echo ""
echo "New routes added (Sovereign-only, except /teams which allows Circle too):"
echo "   GET  /api/engineering/teams"
echo "   POST /api/engineering/consult/{team_key}      (team_key: keel or ballast)"
echo "   POST /api/engineering/consult-both"
echo "   GET  /api/engineering/pending"
echo "   POST /api/engineering/reviewed/{consultation_id}"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp main.py.bak7 main.py"
