#!/bin/bash
set -e
cd ~/the_commons

echo "========================================"
echo " Step 1: Fix corrupted database.py"
echo "========================================"

python3 - << 'PYEOF'
import re

path = "commons/database.py"
with open(path) as f:
    src = f.read()

original = src

broken = re.compile(
    r'([ \t]*)(avatar_url\s*=\s*Column\(String,\s*default=\'\'\))'
    r'\("CommunityVote",\s*back_populates="post"\)'
)
if broken.search(src):
    src = broken.sub(
        lambda m: (
            m.group(1) + m.group(2) + "\n" +
            m.group(1) + 'community_votes = relationship("CommunityVote", back_populates="post")'
        ),
        src,
        count=1
    )
    print("Fixed: avatar_url / CommunityVote line merge")

if "UniqueConstraint" not in src:
    src = src.replace("from sqlalchemy import", "from sqlalchemy import UniqueConstraint,", 1)
    print("Fixed: UniqueConstraint import")

if "class CommunityVote" not in src and "class Vote" not in src:
    vote_model = '''
class CommunityVote(Base):
    __tablename__ = "community_votes"
    id      = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    value   = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_vote"),)
    post = relationship("Post", back_populates="community_votes")
    user = relationship("User")
'''
    src = src.rstrip() + "\n" + vote_model + "\n"
    print("Fixed: CommunityVote model added")

if src == original:
    print("No changes needed")
else:
    with open(path, "w") as f:
        f.write(src)
    print("Saved commons/database.py")
PYEOF

echo "========================================"
echo " Step 2: Syntax check"
echo "========================================"
python3 -m py_compile commons/database.py && echo "database.py OK"
python3 -m py_compile main.py && echo "main.py OK"

echo "========================================"
echo " Step 3: Commit and push"
echo "========================================"
git add -A
git commit -m "fix: repair corrupted database.py CommunityVote line merge"
git push origin main

echo "========================================"
echo " DONE - Render is deploying now"
echo " Watch: https://dashboard.render.com"
echo "========================================"
