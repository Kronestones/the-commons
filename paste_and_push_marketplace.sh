#!/bin/bash
# ============================================================
# paste_and_push_marketplace.sh
# Run this inside ~/the_commons in Termux
# It does everything: patches main.py, copies templates,
# appends CSS, syntax checks, commits, and pushes.
# ============================================================

set -e
cd ~/the_commons

echo ""
echo "📦 Step 1 — Backing up main.py..."
cp main.py main.py.bak.marketplace
echo "✅ Backup saved as main.py.bak.marketplace"


# ============================================================
# STEP 2 — Write the 4 templates
# ============================================================
echo ""
echo "📄 Step 2 — Writing templates..."

cat > templates/marketplace.html << 'ENDOFFILE'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Marketplace — The Commons</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>

{% include "nav.html" %}

<div class="marketplace-container">

  <div class="marketplace-hero card">
    <h1>Marketplace</h1>
    <p class="giving-tagline">Local creators and small businesses only. No corporations. Flat $1 platform fee per transaction.</p>
    <p><strong>The marketplace is open.</strong></p>
  </div>

  <div class="marketplace-toolbar">
    <form method="GET" action="/marketplace" style="flex:1; display:flex; gap:0.5rem;">
      <input
        type="text"
        name="q"
        value="{{ q }}"
        placeholder="Search listings…"
        style="flex:1; padding:0.55rem 0.9rem; border:1px solid #ccc; border-radius:6px; font-size:0.95rem;"
      >
      <button type="submit" class="btn" style="padding:0.55rem 1rem;">Search</button>
    </form>
    {% if current_user %}
      <a href="/marketplace/create" class="btn" style="white-space:nowrap;">+ Post listing</a>
      <a href="/marketplace/inbox" class="btn-secondary" style="white-space:nowrap;">Inbox</a>
    {% else %}
      <a href="/login" class="btn-secondary">Log in to sell</a>
    {% endif %}
  </div>

  {% if listings %}
    <div class="listing-grid">
      {% for listing in listings %}
        <a href="/marketplace/{{ listing.id }}" class="listing-card">
          <div class="listing-img">
            {% if listing.media_path %}
              <img src="{{ listing.media_path }}" alt="{{ listing.title }}">
            {% else %}
              <span class="listing-img-placeholder">🛍️</span>
            {% endif %}
          </div>
          <div class="listing-body">
            <div class="listing-price">
              {% if listing.price == 0 %}Free{% else %}${{ "%.2f"|format(listing.price) }}{% endif %}
            </div>
            <div class="listing-title">{{ listing.title }}</div>
            <div class="listing-seller">
              <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                <circle cx="12" cy="7" r="4"/>
              </svg>
              {{ listing.seller.username }}
            </div>
          </div>
        </a>
      {% endfor %}
    </div>
  {% else %}
    <div class="card" style="text-align:center; padding:3rem 2rem; color:#888;">
      <div style="font-size:3rem; margin-bottom:1rem;">🛍️</div>
      <h3 style="color:#1a4a2e; margin-bottom:0.5rem;">
        {% if q %}No listings match "{{ q }}"{% else %}Be the first to list a product.{% endif %}
      </h3>
      {% if current_user %}
        <a href="/marketplace/create" class="btn" style="margin-top:1rem; display:inline-block;">Post a listing</a>
      {% endif %}
    </div>
  {% endif %}

</div>
</body>
</html>
ENDOFFILE

cat > templates/marketplace_create.html << 'ENDOFFILE'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Post a Listing — The Commons</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>

{% include "nav.html" %}

<div class="form-container">
  <div class="card" style="padding:2rem;">
    <h2 class="section-heading" style="margin-top:0;">Post a listing</h2>

    {% if error %}
      <div class="error-msg">{{ error }}</div>
    {% endif %}

    <form method="POST" action="/marketplace/create" enctype="multipart/form-data">

      <label for="photo">Photo (optional)</label>
      <input
        type="file"
        id="photo"
        name="photo"
        accept="image/*"
        onchange="previewPhoto(this)"
        style="display:block; margin-bottom:0.5rem;"
      >
      <img id="photo-preview" src="" alt="" style="display:none; width:120px; height:120px; object-fit:cover; border-radius:8px; margin-bottom:1rem; border:1px solid #ddd;">

      <label for="title">Title *</label>
      <input type="text" id="title" name="title" placeholder="What are you selling?" required>

      <label for="price">Price ($)</label>
      <input type="number" id="price" name="price" placeholder="0.00" min="0" step="0.01" value="0">
      <small style="color:#888; display:block; margin-top:0.2rem; margin-bottom:0.8rem;">Enter 0 for free / donation.</small>

      <label for="description">Description</label>
      <textarea id="description" name="description" placeholder="Condition, size, pickup details…"></textarea>

      <div style="margin-top:1.5rem; display:flex; gap:0.75rem; align-items:center;">
        <button type="submit" class="btn">Post listing</button>
        <a href="/marketplace" class="btn-secondary">Cancel</a>
      </div>

    </form>
  </div>
</div>

<script>
function previewPhoto(input) {
  const preview = document.getElementById('photo-preview');
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      preview.src = e.target.result;
      preview.style.display = 'block';
    };
    reader.readAsDataURL(input.files[0]);
  }
}
</script>
</body>
</html>
ENDOFFILE

cat > templates/marketplace_detail.html << 'ENDOFFILE'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ listing.title }} — The Commons Marketplace</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>

{% include "nav.html" %}

<div class="marketplace-container" style="max-width:680px;">

  <a href="/marketplace" class="btn-secondary" style="display:inline-block; margin-bottom:1rem;">← Back to Marketplace</a>

  <div class="card" style="padding:0; overflow:hidden;">

    {% if listing.media_path %}
      <img src="{{ listing.media_path }}" alt="{{ listing.title }}"
           style="width:100%; max-height:360px; object-fit:cover; display:block;">
    {% endif %}

    <div style="padding:1.5rem;">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:1rem;">
        <div>
          <h2 style="margin:0 0 0.25rem; color:#1a4a2e;">{{ listing.title }}</h2>
          <div style="font-size:1.4rem; font-weight:700; color:#1a4a2e; margin-bottom:0.5rem;">
            {% if listing.price == 0 %}Free{% else %}${{ "%.2f"|format(listing.price) }}{% endif %}
          </div>
        </div>
        {% if is_seller %}
          <form method="POST" action="/marketplace/{{ listing.id }}/delete"
                onsubmit="return confirm('Delete this listing?');">
            <button type="submit" class="btn-secondary" style="color:#c0392b; border-color:#c0392b; font-size:0.85rem;">
              Delete listing
            </button>
          </form>
        {% endif %}
      </div>

      <div class="listing-seller" style="margin-bottom:1rem;">
        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        Listed by
        <a href="/profile/{{ listing.seller.username }}" class="username-link">{{ listing.seller.username }}</a>
      </div>

      {% if listing.description %}
        <p style="color:#333; line-height:1.6; white-space:pre-wrap;">{{ listing.description }}</p>
      {% endif %}
    </div>
  </div>

  {% if current_user and not is_seller %}
    <div class="card" style="margin-top:1.25rem; padding:1.5rem;">
      <h3 class="section-heading" style="margin-top:0;">Message seller</h3>
      <div class="msg-thread" id="msg-thread">
        {% if thread %}
          {% for msg in thread %}
            <div class="bubble {% if msg.sender_id == current_user.id %}sent{% else %}received{% endif %}">
              {{ msg.body }}
            </div>
          {% endfor %}
        {% else %}
          <p class="muted" style="text-align:center; padding:1rem 0;">
            Ask a question — the seller will reply here.
          </p>
        {% endif %}
      </div>
      <form method="POST" action="/marketplace/{{ listing.id }}/message"
            style="display:flex; gap:0.5rem; margin-top:0.75rem;">
        <input
          type="text"
          name="body"
          placeholder="Is this still available?"
          required
          style="flex:1; padding:0.6rem 1rem; border:1px solid #ccc; border-radius:24px; font-size:0.9rem; outline:none;"
        >
        <button type="submit" class="btn" style="border-radius:24px; padding:0.6rem 1.2rem;">Send</button>
      </form>
    </div>
  {% elif is_seller and thread %}
    <div class="card" style="margin-top:1.25rem; padding:1.5rem;">
      <h3 class="section-heading" style="margin-top:0;">
        Messages
        <a href="/marketplace/inbox" class="btn-secondary" style="font-size:0.8rem; margin-left:0.5rem;">View all</a>
      </h3>
      <div class="msg-thread">
        {% for msg in thread %}
          <div class="bubble {% if msg.sender_id == current_user.id %}sent{% else %}received{% endif %}">
            {{ msg.body }}
          </div>
        {% endfor %}
      </div>
    </div>
  {% elif not current_user %}
    <div class="card" style="margin-top:1.25rem; padding:1.5rem; text-align:center;">
      <p class="muted">
        <a href="/login" class="username-link">Log in</a> to message the seller.
      </p>
    </div>
  {% endif %}

</div>

<script>
  const thread = document.getElementById('msg-thread');
  if (thread) thread.scrollTop = thread.scrollHeight;
</script>
</body>
</html>
ENDOFFILE

cat > templates/marketplace_inbox.html << 'ENDOFFILE'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Marketplace Inbox — The Commons</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>

{% include "nav.html" %}

<div class="marketplace-container" style="max-width:680px;">

  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem;">
    <h2 style="margin:0; color:#1a4a2e;">Marketplace Inbox</h2>
    <a href="/marketplace" class="btn-secondary">← Marketplace</a>
  </div>

  {% if threads %}
    <div style="display:flex; flex-direction:column; gap:0.75rem;">
      {% for t in threads %}
        <a href="/marketplace/{{ t.listing.id }}" style="text-decoration:none; color:inherit;">
          <div class="card" style="padding:1rem 1.25rem; display:flex; gap:1rem; align-items:center;
               {% if t.unread %}border-left:3px solid #1a4a2e;{% endif %}">
            {% if t.listing.media_path %}
              <img src="{{ t.listing.media_path }}" alt=""
                   style="width:56px; height:56px; object-fit:cover; border-radius:8px; flex-shrink:0;">
            {% else %}
              <div style="width:56px; height:56px; background:#eaf4ee; border-radius:8px;
                          display:flex; align-items:center; justify-content:center;
                          font-size:1.5rem; flex-shrink:0;">🛍️</div>
            {% endif %}
            <div style="flex:1; min-width:0;">
              <div style="font-weight:{% if t.unread %}700{% else %}500{% endif %}; color:#1a4a2e; margin-bottom:2px;">
                {{ t.listing.title }}
                {% if t.unread %}<span style="background:#1a4a2e; color:#fff; font-size:0.65rem; padding:1px 7px; border-radius:10px; margin-left:6px; vertical-align:middle;">New</span>{% endif %}
              </div>
              <div style="font-size:0.875rem; color:#555; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                {{ t.last_message }}
              </div>
              <div style="font-size:0.75rem; color:#999; margin-top:3px;">
                {% if t.listing.price == 0 %}Free{% else %}${{ "%.2f"|format(t.listing.price) }}{% endif %}
                · {{ t.last_message_at.strftime('%b %-d') }}
              </div>
            </div>
            <div style="color:#ccc;">›</div>
          </div>
        </a>
      {% endfor %}
    </div>
  {% else %}
    <div class="card" style="text-align:center; padding:3rem 2rem; color:#888;">
      <div style="font-size:2.5rem; margin-bottom:0.75rem;">💬</div>
      <p>No messages yet. Browse the <a href="/marketplace" class="username-link">marketplace</a> and reach out to a seller.</p>
    </div>
  {% endif %}

</div>
</body>
</html>
ENDOFFILE

echo "✅ All 4 templates written"


# ============================================================
# STEP 3 — Append marketplace CSS
# ============================================================
echo ""
echo "🎨 Step 3 — Appending marketplace CSS to static/style.css..."

cat >> static/style.css << 'ENDOFFILE'

/* ============================================================
   MARKETPLACE — appended by paste_and_push_marketplace.sh
   ============================================================ */

.marketplace-container {
  max-width: 1100px;
  margin: 2rem auto;
  padding: 0 1rem;
}

.marketplace-hero {
  padding: 2rem;
  margin-bottom: 1.25rem;
  text-align: center;
}

.marketplace-hero h1 {
  font-size: 2rem;
  color: var(--green, #1a4a2e);
  margin-bottom: 0.4rem;
}

.marketplace-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.listing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 1rem;
}

.listing-card {
  background: #fff;
  border: 1px solid #dde8e2;
  border-radius: 10px;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  display: flex;
  flex-direction: column;
  transition: transform 0.12s, box-shadow 0.12s;
  box-shadow: 0 2px 8px rgba(26,58,42,0.07);
}

.listing-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(26,58,42,0.13);
}

.listing-img {
  width: 100%;
  aspect-ratio: 1;
  background: #eaf4ee;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.listing-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.listing-img-placeholder {
  font-size: 2.5rem;
  opacity: 0.6;
}

.listing-body {
  padding: 0.75rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.listing-price {
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--green, #1a4a2e);
}

.listing-title {
  font-size: 0.875rem;
  line-height: 1.35;
  color: #222;
}

.listing-seller {
  font-size: 0.775rem;
  color: #888;
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.msg-thread {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 280px;
  overflow-y: auto;
  padding: 0.25rem 0;
  margin-bottom: 0.5rem;
}

.bubble {
  max-width: 78%;
  padding: 0.55rem 0.9rem;
  border-radius: 16px;
  font-size: 0.875rem;
  line-height: 1.45;
  word-break: break-word;
}

.bubble.sent {
  align-self: flex-end;
  background: var(--green, #1a4a2e);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.bubble.received {
  align-self: flex-start;
  background: #f0f4f2;
  color: #222;
  border: 1px solid #dde8e2;
  border-bottom-left-radius: 4px;
}
ENDOFFILE

echo "✅ CSS appended"


# ============================================================
# STEP 4 — Patch main.py with Python
# ============================================================
echo ""
echo "🔧 Step 4 — Patching main.py..."

python3 << 'PYEOF'
import sys

with open("main.py", "r") as f:
    src = f.read()

# ── Check for existing marketplace patch ──────────────────────────────────────
if "class Listing(Base):" in src:
    print("⚠️  Listing model already exists in main.py — skipping model patch.")
    print("   If you want to re-patch, restore main.py.bak.marketplace and run again.")
    sys.exit(0)

# ── 1. Add imports if missing ─────────────────────────────────────────────────
missing_imports = []
if "from sqlalchemy import" in src and "Float" not in src:
    src = src.replace(
        "from sqlalchemy import",
        "from sqlalchemy import Float, Text, Boolean,  # marketplace\n# noqa\nfrom sqlalchemy import"
    )
# Simpler: just append needed imports at top if not present
needed = [
    ("import shutil",  "import shutil"),
    ("import uuid",    "import uuid"),
    ("import os",      "import os"),
]
insert_after = "from sqlalchemy"
lines = src.split("\n")
last_import_line = 0
for i, line in enumerate(lines):
    if line.startswith("import ") or line.startswith("from "):
        last_import_line = i

additions = []
for check, stmt in needed:
    if check not in src:
        additions.append(stmt)

if additions:
    lines.insert(last_import_line + 1, "\n".join(additions) + "  # marketplace additions")
    src = "\n".join(lines)
    print(f"   Added imports: {', '.join(a for a,_ in needed if a not in src)}")

# ── 2. Add Float, Text, Boolean to sqlalchemy import if missing ───────────────
if "from sqlalchemy import" in src:
    import re
    def add_to_sa_import(src, name):
        if name not in src:
            src = re.sub(
                r"(from sqlalchemy import )([^\n]+)",
                lambda m: m.group(1) + m.group(2).rstrip() + f", {name}",
                src, count=1
            )
        return src
    for name in ["Float", "Text", "Boolean"]:
        src = add_to_sa_import(src, name)

# ── 3. Add MEDIA_DIR after existing os.makedirs or after imports ──────────────
MEDIA_DIR_BLOCK = '''
MEDIA_DIR = "static/media/marketplace"
os.makedirs(MEDIA_DIR, exist_ok=True)
'''
if 'MEDIA_DIR' not in src:
    if 'os.makedirs' in src:
        # Insert after the last os.makedirs line
        idx = src.rfind('os.makedirs')
        end = src.find('\n', idx)
        src = src[:end+1] + MEDIA_DIR_BLOCK + src[end+1:]
    else:
        # Insert before first route definition or class definition
        idx = src.find('\nclass ')
        if idx == -1:
            idx = src.find('\nasync def ')
        src = src[:idx] + MEDIA_DIR_BLOCK + src[idx:]
    print("   Added MEDIA_DIR setup")

# ── 4. Add Listing + ListingMessage models before routes = [ ──────────────────
MODELS = '''

class Listing(Base):
    __tablename__ = "listings"
    id          = Column(Integer, primary_key=True)
    title       = Column(String, nullable=False)
    description = Column(Text, default="")
    price       = Column(Float, nullable=False, default=0.0)
    media_path  = Column(String, default=None)
    seller_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    seller      = relationship("User", backref="listings")
    messages    = relationship("ListingMessage", back_populates="listing", cascade="all, delete-orphan")


class ListingMessage(Base):
    __tablename__ = "listing_messages"
    id           = Column(Integer, primary_key=True)
    listing_id   = Column(Integer, ForeignKey("listings.id"), nullable=False)
    sender_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    body         = Column(Text, nullable=False)
    is_read      = Column(Boolean, default=False)
    created_at   = Column(DateTime, default=datetime.utcnow)
    listing      = relationship("Listing", back_populates="messages")
    sender       = relationship("User", foreign_keys=[sender_id])
    recipient    = relationship("User", foreign_keys=[recipient_id])

'''

# Insert models before routes = [
if "routes = [" in src:
    src = src.replace("routes = [", MODELS + "routes = [", 1)
    print("   Added Listing and ListingMessage models")
else:
    print("   ⚠️  Could not find 'routes = [' — models NOT inserted. Add manually.")

# ── 5. Add handlers before routes = [ ─────────────────────────────────────────
HANDLERS = '''
async def marketplace_page(request):
    db = next(get_db())
    current_user = get_current_user(request, db)
    q = request.query_params.get("q", "").strip()
    query = db.query(Listing).filter(Listing.is_active == True).order_by(Listing.created_at.desc())
    if q:
        like = f"%{q}%"
        query = query.filter(Listing.title.ilike(like) | Listing.description.ilike(like))
    listings = query.all()
    return templates.TemplateResponse("marketplace.html", {
        "request": request, "current_user": current_user,
        "listings": listings, "q": q,
    })


async def marketplace_create(request):
    db = next(get_db())
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    if request.method == "GET":
        return templates.TemplateResponse("marketplace_create.html", {
            "request": request, "current_user": current_user, "error": None,
        })
    form = await request.form()
    title       = (form.get("title") or "").strip()
    description = (form.get("description") or "").strip()
    price_raw   = (form.get("price") or "0").strip()
    photo       = form.get("photo")
    if not title:
        return templates.TemplateResponse("marketplace_create.html", {
            "request": request, "current_user": current_user, "error": "Title is required.",
        })
    try:
        price = float(price_raw)
    except ValueError:
        price = 0.0
    media_path = None
    if photo and getattr(photo, "filename", None):
        ext = photo.filename.rsplit(".", 1)[-1].lower()
        if ext in {"jpg", "jpeg", "png", "webp", "gif"}:
            filename = f"{uuid.uuid4().hex}.{ext}"
            dest = os.path.join(MEDIA_DIR, filename)
            with open(dest, "wb") as f:
                shutil.copyfileobj(photo.file, f)
            media_path = f"/static/media/marketplace/{filename}"
    listing = Listing(title=title, description=description, price=price,
                      media_path=media_path, seller_id=current_user.id)
    db.add(listing)
    db.commit()
    return RedirectResponse("/marketplace", status_code=302)


async def marketplace_detail(request):
    db = next(get_db())
    current_user = get_current_user(request, db)
    listing_id = int(request.path_params["listing_id"])
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    thread = []
    if current_user:
        thread = (
            db.query(ListingMessage)
            .filter(
                ListingMessage.listing_id == listing_id,
                (ListingMessage.sender_id == current_user.id) |
                (ListingMessage.recipient_id == current_user.id)
            )
            .order_by(ListingMessage.created_at.asc()).all()
        )
        for m in thread:
            if m.recipient_id == current_user.id and not m.is_read:
                m.is_read = True
        db.commit()
    return templates.TemplateResponse("marketplace_detail.html", {
        "request": request, "current_user": current_user,
        "listing": listing, "thread": thread,
        "is_seller": current_user and current_user.id == listing.seller_id,
    })


async def marketplace_send_message(request):
    db = next(get_db())
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    listing_id = int(request.path_params["listing_id"])
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return RedirectResponse("/marketplace", status_code=302)
    if listing.seller_id == current_user.id:
        return RedirectResponse(f"/marketplace/{listing_id}", status_code=302)
    form = await request.form()
    body = (form.get("body") or "").strip()
    if body:
        msg = ListingMessage(listing_id=listing_id, sender_id=current_user.id,
                             recipient_id=listing.seller_id, body=body)
        db.add(msg)
        db.commit()
    return RedirectResponse(f"/marketplace/{listing_id}", status_code=302)


async def marketplace_inbox(request):
    db = next(get_db())
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    all_msgs = (
        db.query(ListingMessage)
        .filter(
            (ListingMessage.sender_id == current_user.id) |
            (ListingMessage.recipient_id == current_user.id)
        )
        .order_by(ListingMessage.created_at.desc()).all()
    )
    seen = {}
    threads = []
    for m in all_msgs:
        if m.listing_id not in seen:
            seen[m.listing_id] = True
            threads.append({
                "listing": m.listing, "last_message": m.body,
                "last_message_at": m.created_at,
                "unread": (not m.is_read and m.recipient_id == current_user.id),
            })
    return templates.TemplateResponse("marketplace_inbox.html", {
        "request": request, "current_user": current_user, "threads": threads,
    })


async def marketplace_delete(request):
    db = next(get_db())
    current_user = get_current_user(request, db)
    if not current_user:
        return RedirectResponse("/login", status_code=302)
    listing_id = int(request.path_params["listing_id"])
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if listing and listing.seller_id == current_user.id:
        db.delete(listing)
        db.commit()
    return RedirectResponse("/marketplace", status_code=302)

'''

if "routes = [" in src:
    src = src.replace("routes = [", HANDLERS + "routes = [", 1)
    print("   Added marketplace handlers")

# ── 6. Add new routes inside routes = [ ──────────────────────────────────────
NEW_ROUTES = '''    Route("/marketplace",                         marketplace_page),
    Route("/marketplace/create",                  marketplace_create,        methods=["GET", "POST"]),
    Route("/marketplace/inbox",                   marketplace_inbox),
    Route("/marketplace/{listing_id:int}",        marketplace_detail),
    Route("/marketplace/{listing_id:int}/message",marketplace_send_message,  methods=["POST"]),
    Route("/marketplace/{listing_id:int}/delete", marketplace_delete,        methods=["POST"]),'''

# Find and replace the old single /marketplace route
import re
old_marketplace_route = re.search(r'[ \t]*Route\("/marketplace"[^\n]*\),?\n', src)
if old_marketplace_route:
    src = src[:old_marketplace_route.start()] + NEW_ROUTES + "\n" + src[old_marketplace_route.end():]
    print("   Replaced old /marketplace route with 6 new marketplace routes")
elif "routes = [" in src:
    # Fallback: insert at start of routes list
    src = src.replace("routes = [\n", "routes = [\n" + NEW_ROUTES + "\n", 1)
    print("   Added 6 marketplace routes to routes list")
else:
    print("   ⚠️  Could not find routes list — add routes manually.")

with open("main.py", "w") as f:
    f.write(src)

print("   main.py written successfully")
PYEOF

PATCH_EXIT=$?
if [ $PATCH_EXIT -ne 0 ]; then
  echo "❌ Python patch failed — restoring backup"
  cp main.py.bak.marketplace main.py
  exit 1
fi


# ============================================================
# STEP 5 — Syntax check
# ============================================================
echo ""
echo "🔍 Step 5 — Syntax checking main.py..."
python3 -m py_compile main.py && echo "✅ Syntax OK" || {
  echo "❌ Syntax error found — restoring backup"
  cp main.py.bak.marketplace main.py
  echo "   Your original main.py has been restored."
  echo "   Check the error above and fix manually."
  exit 1
}


# ============================================================
# STEP 6 — Commit and push
# ============================================================
echo ""
echo "🚀 Step 6 — Committing and pushing..."
git add -A
git commit -m "feat: marketplace listings, photo upload, in-app messaging"
git push origin main

echo ""
echo "============================================================"
echo "✅ All done! Render is deploying now."
echo ""
echo "Test these URLs once it's live:"
echo "  → https://the-commons.onrender.com/marketplace"
echo "  → https://the-commons.onrender.com/marketplace/create"
echo "  → https://the-commons.onrender.com/marketplace/inbox"
echo "============================================================"
