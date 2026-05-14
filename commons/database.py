"""
database.py — The Commons Database

SQLite for development. PostgreSQL ready for production.
All state written to disk. Nothing held only in memory.
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Boolean,
    DateTime, Float, ForeignKey, Enum
)
try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
from .config import config

engine = create_engine(
    config.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in config.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Enums ─────────────────────────────────────────────────────────────────────

class PostStatus(str, enum.Enum):
    PENDING     = "pending"      # Awaiting Fingerprint check
    PUBLISHED   = "published"    # Verified and live
    HELD        = "held"         # Flagged, awaiting human review
    REMOVED     = "removed"      # Confirmed false — removed
    APPEALED    = "appealed"     # Removal appealed to Circle

class PostType(str, enum.Enum):
    TEXT        = "text"
    IMAGE       = "image"
    VIDEO       = "video"
    AUDIO       = "audio"
    LIVE        = "live"

class AlgorithmMode(str, enum.Enum):
    TRANSPARENT     = "transparent"
    CHRONOLOGICAL   = "chronological"
    COMMUNITY       = "community"

class UserRole(str, enum.Enum):
    USER        = "user"
    CREATOR     = "creator"
    SELLER      = "seller"
    CIRCLE      = "circle"
    SOVEREIGN   = "sovereign"

class VoteChoice(str, enum.Enum):
    AYE         = "aye"
    NAY         = "nay"
    ABSTAIN     = "abstain"


# ── Models ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50), unique=True, index=True, nullable=False)
    email           = Column(String(255), unique=True, index=True, nullable=False)
    password_hash   = Column(String(255), nullable=False)
    display_name    = Column(String(100))
    bio             = Column(Text, default="")
    avatar_path     = Column(String(500), nullable=True)
    banner_path     = Column(String(500), nullable=True)
    role            = Column(Enum(UserRole), default=UserRole.USER)
    algorithm_mode  = Column(Enum(AlgorithmMode), default=AlgorithmMode.TRANSPARENT)
    is_active       = Column(Boolean, default=True)
    is_minor        = Column(Boolean, default=False)
    is_verified     = Column(Boolean, default=False)  # Blue checkmark at 10k followers
    created_at      = Column(DateTime, default=datetime.utcnow)
    last_seen       = Column(DateTime, default=datetime.utcnow)

    # No biometrics — ever
    # No phone number required
    # No behavioral profile

    posts           = relationship("Post", back_populates="author")
    votes           = relationship("CommunityVote", back_populates="user")


class Post(Base):
    __tablename__ = "posts"

    id              = Column(Integer, primary_key=True, index=True)
    author_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_type       = Column(Enum(PostType), nullable=False)
    content         = Column(Text, default="")
    media_path      = Column(String(500), default="")
    status          = Column(Enum(PostStatus), default=PostStatus.PENDING)
    is_news         = Column(Boolean, default=False)   # Triggers Fingerprint
    is_political    = Column(Boolean, default=False)   # Triggers Fingerprint
    community_score = Column(Float, default=0.0)       # Community value score
    view_count      = Column(Integer, default=0)
    created_at      = Column(DateTime, default=datetime.utcnow)
    published_at    = Column(DateTime, nullable=True)

    author          = relationship("User", back_populates="posts")
    fingerprint     = relationship("FingerprintRecord", back_populates="post", uselist=False)
    community_votes = relationship("CommunityVote", back_populates="post")
    product_tags    = relationship("ProductTag", back_populates="post")


class FingerprintRecord(Base):
    __tablename__ = "fingerprint_records"

    id              = Column(Integer, primary_key=True, index=True)
    post_id         = Column(Integer, ForeignKey("posts.id"), unique=True)
    scan_result     = Column(String(20), default="pending")  # clean/flagged/held
    claims_found    = Column(Text, default="[]")             # JSON list of claims
    deepfake_score  = Column(Float, default=0.0)             # 0-1, higher = more suspicious
    manipulation_score = Column(Float, default=0.0)
    reviewer        = Column(String(100), nullable=True)
    reviewer_notes  = Column(Text, default="")
    decision        = Column(String(20), nullable=True)      # verified/removed
    decision_reason = Column(Text, default="")
    scanned_at      = Column(DateTime, default=datetime.utcnow)
    decided_at      = Column(DateTime, nullable=True)

    post            = relationship("Post", back_populates="fingerprint")


class CircleMember(Base):
    __tablename__ = "circle_members"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True)
    seat_type       = Column(String(50))   # global / regional / community
    region          = Column(String(100), default="global")
    is_head         = Column(Boolean, default=False)
    elected_at      = Column(DateTime, default=datetime.utcnow)
    term_ends       = Column(DateTime, nullable=True)
    votes_cast      = Column(Integer, default=0)


class CircleDecision(Base):
    __tablename__ = "circle_decisions"

    id              = Column(Integer, primary_key=True, index=True)
    subject         = Column(String(255))
    decision_type   = Column(String(50))   # appeal / codex_amendment / removal / other
    post_id         = Column(Integer, ForeignKey("posts.id"), nullable=True)
    outcome         = Column(String(50), nullable=True)
    ayes            = Column(Integer, default=0)
    nays            = Column(Integer, default=0)
    abstentions     = Column(Integer, default=0)
    dissent_notes   = Column(Text, default="")   # Minority opinion always recorded
    reasoning       = Column(Text, default="")
    created_at      = Column(DateTime, default=datetime.utcnow)
    closed_at       = Column(DateTime, nullable=True)


class CommunityVote(Base):
    __tablename__ = "community_votes"

    id              = Column(Integer, primary_key=True, index=True)
    post_id         = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    value           = Column(Integer, default=1)   # 1 = valued, -1 = not valuable
    created_at      = Column(DateTime, default=datetime.utcnow)

    post            = relationship("Post", back_populates="community_votes")
    user            = relationship("User", back_populates="votes")


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), unique=True)
    business_name   = Column(String(200))
    business_type   = Column(String(50))   # individual / small_business
    is_verified     = Column(Boolean, default=False)
    is_corporation  = Column(Boolean, default=False)   # Must be False — Codex Law 11
    is_publicly_traded = Column(Boolean, default=False) # Must be False — Codex Law 11
    approved_at     = Column(DateTime, nullable=True)


class Product(Base):
    __tablename__ = "products"

    id              = Column(Integer, primary_key=True, index=True)
    seller_id       = Column(Integer, ForeignKey("seller_profiles.id"))
    name            = Column(String(300))
    description     = Column(Text)
    price           = Column(Float, nullable=False)
    media_path      = Column(String(500), default="")
    is_active       = Column(Boolean, default=True)
    community_score = Column(Float, default=0.0)
    created_at      = Column(DateTime, default=datetime.utcnow)

    tags            = relationship("ProductTag", back_populates="product")
    transactions    = relationship("Transaction", back_populates="product")


class ProductTag(Base):
    __tablename__ = "product_tags"

    id              = Column(Integer, primary_key=True, index=True)
    post_id         = Column(Integer, ForeignKey("posts.id"))
    product_id      = Column(Integer, ForeignKey("products.id"))
    timestamp_sec   = Column(Float, default=0.0)   # For video tags

    post            = relationship("Post", back_populates="product_tags")
    product         = relationship("Product", back_populates="tags")


class Order(Base):
    """
    One order = one checkout = one $1 platform fee.
    No matter how many items. Always $1 per sale. Codex Law 12.
    """
    __tablename__ = "orders"

    id              = Column(Integer, primary_key=True, index=True)
    buyer_id        = Column(Integer, ForeignKey("users.id"))
    platform_fee    = Column(Float, default=1.00)  # Always $1. One per order. Codex Law 12.
    items_total     = Column(Float, nullable=False) # Sum of all item prices
    order_total     = Column(Float, nullable=False) # items_total + $1
    status          = Column(String(50), default="pending")
    created_at      = Column(DateTime, default=datetime.utcnow)

    items           = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """
    Individual items within an order.
    Multiple items — still only one $1 fee on the parent Order.
    """
    __tablename__ = "order_items"

    id              = Column(Integer, primary_key=True, index=True)
    order_id        = Column(Integer, ForeignKey("orders.id"))
    product_id      = Column(Integer, ForeignKey("products.id"))
    quantity        = Column(Integer, default=1)
    item_price      = Column(Float, nullable=False)
    line_total      = Column(Float, nullable=False)

    order           = relationship("Order", back_populates="items")
    product         = relationship("Product")


class Transaction(Base):
    __tablename__ = "transactions"

    id              = Column(Integer, primary_key=True, index=True)
    buyer_id        = Column(Integer, ForeignKey("users.id"))
    product_id      = Column(Integer, ForeignKey("products.id"))
    product_price   = Column(Float, nullable=False)
    platform_fee    = Column(Float, default=1.00)  # Always $1. Codex Law 12.
    total           = Column(Float, nullable=False)
    status          = Column(String(50), default="pending")
    created_at      = Column(DateTime, default=datetime.utcnow)

    product         = relationship("Product", back_populates="transactions")


# ── Database Setup ────────────────────────────────────────────────────────────

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    print("[DATABASE] Tables created.")


class Follow(Base):
    __tablename__ = "follows"
    id          = Column(Integer, primary_key=True)
    follower_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    following_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)


class DirectMessage(Base):
    __tablename__ = "direct_messages"
    id          = Column(Integer, primary_key=True)
    sender_id   = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content     = Column(Text, nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    read        = Column(Boolean, default=False)
    request     = Column(Boolean, default=False)  # True = stranger, needs acceptance
    accepted    = Column(Boolean, default=None, nullable=True)  # None=pending, True=accepted, False=declined
