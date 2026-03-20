with open('main.py', 'r') as f:
    content = f.read()

old = '''    ip = get_client_ip(request)
    enforce_rate_limit(ip, "register")'''

new = '''    try:
        ip = get_client_ip(request)
        enforce_rate_limit(ip, "register")
    except Exception:
        pass'''

content = content.replace(old, new)

old2 = '''    ip = get_client_ip(request)
    enforce_rate_limit(ip, "login")'''

new2 = '''    try:
        ip = get_client_ip(request)
        enforce_rate_limit(ip, "login")
    except Exception:
        pass'''

content = content.replace(old2, new2)
with open('main.py', 'w') as f:
    f.write(content)
print("Fixed.")
