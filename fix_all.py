# Fix codex laws
with open('commons/codex.py', 'r') as f:
    content = f.read()
# Fix Open Source law
content = content.replace(
    '"The core codebase of The Commons is open source. The people can see how it works. The people can verify it does what it says."',
    '"The Commons operates transparently — our policies, governance, finances, and Codex are fully public. The platform does what it says it does."'
)
with open('commons/codex.py', 'w') as f:
    f.write(content)
print("Codex fixed.")

# Fix template - Sixteen to Eighteen
with open('templates/codex.html', 'r') as f:
    content = f.read()
content = content.replace('The Sixteen Laws', 'The {{ codex.LAWS|length }} Laws')
with open('templates/codex.html', 'w') as f:
    f.write(content)
print("Template fixed.")

# Fix register route - wrap entire handler in try/except
with open('main.py', 'r') as f:
    content = f.read()
old = '''    result = register_user(db, u["value"], e["value"], password,
                           d["value"], is_minor)
    if not result["ok"]:
        return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
    return JSONResponse({
        "ok":    True,
        "token": result["token"],
        "user":  {"id": result["user"].id, "username": result["user"].username}
    })'''
new = '''    try:
        result = register_user(db, u["value"], e["value"], password,
                               d["value"], is_minor)
        if not result["ok"]:
            return JSONResponse({"ok": False, "error": result["error"]}, status_code=400)
        return JSONResponse({
            "ok":    True,
            "token": result["token"],
            "user":  {"id": result["user"].id, "username": result["user"].username}
        })
    except Exception as ex:
        return JSONResponse({"ok": False, "error": f"Registration failed: {str(ex)}"}, status_code=500)'''
content = content.replace(old, new)
with open('main.py', 'w') as f:
    f.write(content)
print("Register route fixed.")
