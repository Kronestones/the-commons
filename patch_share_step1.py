#!/usr/bin/env python3
"""Share-post step 1:
  (1) add posts.shared_post_id to the LIVE database (safe, nullable, old code keeps working)
  (2) add the matching column + relationship to the Post model
  (3) mask the database password in the startup log line in commons/config.py
Run this BEFORE pushing. Nothing is edited unless the database step succeeds."""
import re, sys, shutil

DB_PY = "commons/database.py"
CFG_PY = "commons/config.py"

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

# ---- plan the file edits first (so we abort before touching anything) ----
db_src = read(DB_PY)
cfg_src = read(CFG_PY)

new_db = None
if "shared_post_id" in db_src:
    print("database.py already has shared_post_id; skipping model edit.")
else:
    m = re.search(r"^class Post\(Base\):.*?(?=^class |\Z)", db_src, flags=re.S | re.M)
    if not m:
        sys.exit("ABORT: class Post not found")
    body = m.group(0)
    pub = list(re.finditer(r"^    published_at\s*=.*$", body, flags=re.M))
    prod = list(re.finditer(r"^    product_tags\s*=.*$", body, flags=re.M))
    if len(pub) != 1 or len(prod) != 1:
        sys.exit("ABORT: could not find published_at / product_tags lines in Post (found %d / %d)"
                 % (len(pub), len(prod)))
    body2 = body
    # insert relationship after product_tags first (later in text), then the column after published_at
    p = prod[0]
    body2 = (body2[:p.end()] +
             '\n    shared_post     = relationship("Post", remote_side=[id], foreign_keys=[shared_post_id])' +
             body2[p.end():])
    p = pub[0]
    body2 = (body2[:p.end()] +
             '\n    shared_post_id  = Column(Integer, ForeignKey("posts.id"), nullable=True)  # set when this post is a share of another post' +
             body2[p.end():])
    new_db = db_src[:m.start()] + body2 + db_src[m.end():]

CFG_OLD = 'print(f"[CONFIG]   Database    : {self.database_url}")'
CFG_NEW = ('_db = self.database_url\n'
           '        try:\n'
           '            from sqlalchemy.engine import make_url\n'
           '            _db = make_url(_db).render_as_string(hide_password=True)\n'
           '        except Exception:\n'
           '            _db = "(hidden)"\n'
           '        print(f"[CONFIG]   Database    : {_db}")')
new_cfg = None
if "_db = self.database_url" in cfg_src:
    print("config.py already masks the database URL; skipping.")
elif cfg_src.count(CFG_OLD) != 1:
    sys.exit("ABORT: config.py database print line found %d times" % cfg_src.count(CFG_OLD))
else:
    new_cfg = cfg_src.replace(CFG_OLD, CFG_NEW)

# ---- (1) database migration ----
from sqlalchemy import text, inspect
from commons.database import engine

if engine.dialect.name != "postgresql":
    sys.exit("ABORT: DATABASE_URL is not Postgres (got %s). Check ~/the_commons/.env" % engine.dialect.name)

insp = inspect(engine)
if not insp.has_table("posts"):
    sys.exit("ABORT: no 'posts' table in this database. Wrong DATABASE_URL? Host: %s" % engine.url.host)
cols = {c["name"] for c in insp.get_columns("posts")}
if not {"author_id", "is_news", "community_score"} <= cols:
    sys.exit("ABORT: this doesn't look like The Commons' posts table. Host: %s" % engine.url.host)

print("Database host:", engine.url.host)
with engine.begin() as conn:
    conn.execute(text("ALTER TABLE posts ADD COLUMN IF NOT EXISTS shared_post_id INTEGER REFERENCES posts(id)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_posts_shared_post_id ON posts(shared_post_id)"))
print("Database: posts.shared_post_id is in place.")

# ---- (2) + (3) write files ----
if new_db is not None:
    write(DB_PY, new_db); print("patched", DB_PY)
if new_cfg is not None:
    write(CFG_PY, new_cfg); print("patched", CFG_PY)
print("Done. (git is your backup: `git diff` shows the changes, `git checkout <file>` undoes them.)")
