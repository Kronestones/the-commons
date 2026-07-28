#!/data/data/com.termux/files/usr/bin/bash
# fix_message_route_order.sh — Fix /api/messages/send being intercepted by
# the /api/messages/{recipient_id} wildcard route registered earlier.
# FastAPI matches routes in registration order, so specific paths must
# come before parameterized wildcard paths.
# Run from ~/the_commons

set -e

if [ ! -f "main.py" ]; then
    echo "❌ Run this from the_commons project root."
    exit 1
fi

echo "📦 Backing up main.py..."
cp main.py main.py.bak4
echo "   -> main.py.bak4"

python3 << 'PYEOF'
path = "main.py"
with open(path, "r") as f:
    src = f.read()

old_wildcard_block = '''@app.post("/api/messages/{recipient_id}")
async def api_send_message(
    recipient_id: int,
    content:      str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(dm_manager.send(db, current_user, recipient_id, content))

@app.get("/api/messages/{other_user_id}/conversation")'''

new_wildcard_block = '''@app.post("/api/messages/send")
async def api_send_message_by_username(
    username: str = Form(...),
    content:  str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(send_message(db, current_user, username, content))

@app.post("/api/messages/{recipient_id}")
async def api_send_message(
    recipient_id: int,
    content:      str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(dm_manager.send(db, current_user, recipient_id, content))

@app.get("/api/messages/{other_user_id}/conversation")'''

if old_wildcard_block not in src:
    print("❌ Could not find the wildcard route block. Aborting — no changes made.")
    raise SystemExit(1)

src = src.replace(old_wildcard_block, new_wildcard_block, 1)

old_duplicate_block = '''@app.post("/api/messages/send")
async def api_send_message(
    username: str = Form(...),
    content:  str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return JSONResponse(send_message(db, current_user, username, content))


@app.get("/api/messages/inbox")'''

new_duplicate_block = '''@app.get("/api/messages/inbox")'''

if old_duplicate_block not in src:
    print("❌ Could not find the duplicate /api/messages/send block further down. Aborting.")
    print("   Please check main.py manually for a leftover duplicate /api/messages/send route.")
    raise SystemExit(1)

src = src.replace(old_duplicate_block, new_duplicate_block, 1)

with open(path, "w") as f:
    f.write(src)

print("✅ main.py patched — /api/messages/send now registered before the {recipient_id} wildcard,")
print("   and the old duplicate lower down was removed.")
PYEOF

echo ""
echo "🎉 Done. Review the diff with:"
echo "   diff main.py.bak4 main.py"
echo ""
echo "If it looks right:"
echo "   git add -A && git commit -m 'Fix message routing: register /api/messages/send before wildcard route'"
echo "   git push"
echo ""
echo "If something looks wrong, restore with:"
echo "   cp main.py.bak4 main.py"
