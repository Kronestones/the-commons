"""
payments.py — The Commons Payment Infrastructure

Multi-currency support. Live stream gifts. Local commerce.
All ready for Stripe connection.

Flat $1 per sale. Always. Codex Law 12.
Surplus donated to humanitarian causes. Codex Law 17.
No profit. Ever.

Multi-currency:
  - Buyers pay in their local currency
  - Sellers receive in their preferred currency
  - Stripe handles conversion automatically
  - The $1 fee is always $1 USD equivalent

Live Gifts:
  - Viewers send virtual gifts during live streams
  - Gifts convert to real value for creators
  - Platform takes nothing from gifts — 100% to creator
  - Gift amounts are small and transparent
  - No dark patterns — no artificial scarcity, no FOMO manipulation

— The Architect, Founder of The Commons · The Commons · 2026
  Power to the People
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Session
from .database import Base

# ── Supported Currencies ──────────────────────────────────────────────────────

SUPPORTED_CURRENCIES = {
    "USD": {"name": "US Dollar",          "symbol": "$",  "flag": "🇺🇸"},
    "EUR": {"name": "Euro",               "symbol": "€",  "flag": "🇪🇺"},
    "GBP": {"name": "British Pound",      "symbol": "£",  "flag": "🇬🇧"},
    "CAD": {"name": "Canadian Dollar",    "symbol": "$",  "flag": "🇨🇦"},
    "AUD": {"name": "Australian Dollar",  "symbol": "$",  "flag": "🇦🇺"},
    "JPY": {"name": "Japanese Yen",       "symbol": "¥",  "flag": "🇯🇵"},
    "CNY": {"name": "Chinese Yuan",       "symbol": "¥",  "flag": "🇨🇳"},
    "INR": {"name": "Indian Rupee",       "symbol": "₹",  "flag": "🇮🇳"},
    "BRL": {"name": "Brazilian Real",     "symbol": "R$", "flag": "🇧🇷"},
    "MXN": {"name": "Mexican Peso",       "symbol": "$",  "flag": "🇲🇽"},
    "KRW": {"name": "South Korean Won",   "symbol": "₩",  "flag": "🇰🇷"},
    "SGD": {"name": "Singapore Dollar",   "symbol": "$",  "flag": "🇸🇬"},
    "CHF": {"name": "Swiss Franc",        "symbol": "Fr", "flag": "🇨🇭"},
    "SEK": {"name": "Swedish Krona",      "symbol": "kr", "flag": "🇸🇪"},
    "NOK": {"name": "Norwegian Krone",    "symbol": "kr", "flag": "🇳🇴"},
    "DKK": {"name": "Danish Krone",       "symbol": "kr", "flag": "🇩🇰"},
    "NZD": {"name": "New Zealand Dollar", "symbol": "$",  "flag": "🇳🇿"},
    "ZAR": {"name": "South African Rand", "symbol": "R",  "flag": "🇿🇦"},
    "NGN": {"name": "Nigerian Naira",     "symbol": "₦",  "flag": "🇳🇬"},
    "KES": {"name": "Kenyan Shilling",    "symbol": "KSh","flag": "🇰🇪"},
    "GHS": {"name": "Ghanaian Cedi",      "symbol": "₵",  "flag": "🇬🇭"},
    "PHP": {"name": "Philippine Peso",    "symbol": "₱",  "flag": "🇵🇭"},
    "IDR": {"name": "Indonesian Rupiah",  "symbol": "Rp", "flag": "🇮🇩"},
    "THB": {"name": "Thai Baht",          "symbol": "฿",  "flag": "🇹🇭"},
    "VND": {"name": "Vietnamese Dong",    "symbol": "₫",  "flag": "🇻🇳"},
    "MYR": {"name": "Malaysian Ringgit",  "symbol": "RM", "flag": "🇲🇾"},
    "PKR": {"name": "Pakistani Rupee",    "symbol": "₨",  "flag": "🇵🇰"},
    "BDT": {"name": "Bangladeshi Taka",   "symbol": "৳",  "flag": "🇧🇩"},
    "EGP": {"name": "Egyptian Pound",     "symbol": "£",  "flag": "🇪🇬"},
    "ARS": {"name": "Argentine Peso",     "symbol": "$",  "flag": "🇦🇷"},
}

# ── Live Gift Types ───────────────────────────────────────────────────────────
# Simple, transparent, no artificial scarcity. No FOMO.

GIFT_TYPES = {
    "heart":      {"name": "Heart",        "emoji": "❤️",  "usd_value": 0.10},
    "star":       {"name": "Star",         "emoji": "⭐",  "usd_value": 0.50},
    "flower":     {"name": "Flower",       "emoji": "🌸",  "usd_value": 1.00},
    "spark":      {"name": "Spark",        "emoji": "✨",  "usd_value": 2.00},
    "rainbow":    {"name": "Rainbow",      "emoji": "🌈",  "usd_value": 5.00},
    "sunrise":    {"name": "Sunrise",      "emoji": "🌅",  "usd_value": 10.00},
    "community":  {"name": "Community",    "emoji": "🏡",  "usd_value": 20.00},
}


# ── Payment Processing Fees ──────────────────────────────────────────────────
# Stripe standard processing fees — paid by buyer, passed to Stripe.
# The Commons never keeps processing fees. Full transparency at checkout.

STRIPE_PERCENT = 0.029   # 2.9%
STRIPE_FIXED   = 0.30    # $0.30 per transaction

# ── Legal Disclaimer ─────────────────────────────────────────────────────────

FACILITATOR_DISCLAIMER = (
    "The Commons is a payment facilitator only. "
    "We connect buyers and sellers but are not a party to any transaction. "
    "The Commons is not responsible for the quality, safety, legality, "
    "or delivery of any product or service listed on this platform. "
    "All disputes are between the buyer and seller directly. "
    "By completing a purchase you acknowledge that The Commons "
    "acts solely as a technology intermediary."
)

SELLER_DISCLAIMER = (
    "By listing on The Commons marketplace you agree that: "
    "you are solely responsible for your products and services; "
    "The Commons is not liable for any buyer disputes, chargebacks, "
    "or claims arising from your listings; "
    "you will resolve disputes directly with buyers in good faith."
)


def calculate_processing_fee(amount_usd: float) -> float:
    """Calculate Stripe processing fee for a transaction."""
    return round((amount_usd * STRIPE_PERCENT) + STRIPE_FIXED, 2)

def build_checkout_breakdown(product_price: float = 0.0,
                              platform_fee: float = 1.00,
                              gift_value: float = 0.0) -> dict:
    """
    Build a fully transparent checkout breakdown.
    No surprises. No hidden fees. Codex Law 5.
    Buyer sees exactly where every cent goes before paying.
    """
    subtotal         = product_price + platform_fee + gift_value
    processing_fee   = calculate_processing_fee(subtotal)
    total            = round(subtotal + processing_fee, 2)

    lines = []

    if product_price > 0:
        lines.append({
            "label":       "Product price",
            "amount":      f"${product_price:.2f}",
            "goes_to":     "Seller — 100%"
        })

    if gift_value > 0:
        lines.append({
            "label":       "Gift amount",
            "amount":      f"${gift_value:.2f}",
            "goes_to":     "Creator — 100%"
        })

    if platform_fee > 0:
        lines.append({
            "label":       "Platform fee",
            "amount":      f"${platform_fee:.2f}",
            "goes_to":     "The Commons — operating costs only, no profit"
        })

    lines.append({
        "label":       "Payment processing",
        "amount":      f"${processing_fee:.2f}",
        "goes_to":     "Stripe — 2.9% + $0.30, standard card processing"
    })

    lines.append({
        "label":       "Total",
        "amount":      f"${total:.2f}",
        "goes_to":     "Breakdown shown above — nothing hidden"
    })

    return {
        "breakdown":       lines,
        "total_usd":       total,
        "processing_fee":  processing_fee,
        "transparency_note": (
            "Every dollar is accounted for. "
            "The Commons takes only the $1 platform fee to cover operating costs. "
            "Payment processing fees go directly to Stripe. "
            "No profit. Ever. Codex Law 12."
        ),
        "legal_notice": FACILITATOR_DISCLAIMER,
    }


# ── Models ────────────────────────────────────────────────────────────────────

class UserCurrencyPreference(Base):
    """User's preferred currency for buying and selling."""
    __tablename__ = "user_currency_preferences"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), unique=True)
    preferred_currency  = Column(String(3), default="USD")
    updated_at          = Column(DateTime, default=datetime.utcnow)


class LiveGift(Base):
    """
    A gift sent during a live stream.
    100% goes to the creator. Platform takes nothing from gifts.
    No dark patterns. No artificial scarcity.
    """
    __tablename__ = "live_gifts"

    id              = Column(Integer, primary_key=True, index=True)
    live_post_id    = Column(Integer, ForeignKey("posts.id"), nullable=False)
    sender_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    creator_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    gift_type       = Column(String(50), nullable=False)
    gift_emoji      = Column(String(10), default="❤️")
    usd_value       = Column(Float, nullable=False)
    currency_paid   = Column(String(3), default="USD")
    amount_paid     = Column(Float, nullable=False)
    message         = Column(String(200), default="")
    created_at      = Column(DateTime, default=datetime.utcnow)
    stripe_payment_id = Column(String(255), nullable=True)  # Set when Stripe connected


class CreatorWallet(Base):
    """
    Tracks creator earnings from gifts.
    Ready for Stripe payout connection.
    """
    __tablename__ = "creator_wallets"

    id              = Column(Integer, primary_key=True, index=True)
    creator_id      = Column(Integer, ForeignKey("users.id"), unique=True)
    balance_usd     = Column(Float, default=0.0)
    total_earned    = Column(Float, default=0.0)
    last_payout     = Column(DateTime, nullable=True)
    preferred_currency = Column(String(3), default="USD")
    stripe_account_id  = Column(String(255), nullable=True)  # Set when Stripe connected
    updated_at      = Column(DateTime, default=datetime.utcnow)


# ── Payment Manager ───────────────────────────────────────────────────────────

class PaymentManager:

    def get_supported_currencies(self) -> list:
        return [
            {
                "code":   code,
                "name":   info["name"],
                "symbol": info["symbol"],
                "flag":   info["flag"],
            }
            for code, info in SUPPORTED_CURRENCIES.items()
        ]

    def set_currency_preference(self, db: Session,
                                user_id: int,
                                currency: str) -> dict:
        """Set a user's preferred currency."""
        if currency not in SUPPORTED_CURRENCIES:
            return {"ok": False, "error": f"Currency '{currency}' not supported."}

        pref = db.query(UserCurrencyPreference).filter(
            UserCurrencyPreference.user_id == user_id
        ).first()

        if pref:
            pref.preferred_currency = currency
            pref.updated_at         = datetime.utcnow()
        else:
            db.add(UserCurrencyPreference(
                user_id            = user_id,
                preferred_currency = currency,
            ))
        db.commit()
        return {
            "ok":       True,
            "currency": currency,
            "name":     SUPPORTED_CURRENCIES[currency]["name"],
        }

    def get_currency_preference(self, db: Session, user_id: int) -> str:
        pref = db.query(UserCurrencyPreference).filter(
            UserCurrencyPreference.user_id == user_id
        ).first()
        return pref.preferred_currency if pref else "USD"

    def format_price(self, usd_amount: float, currency: str,
                     include_platform_fee: bool = True) -> dict:
        """
        Format a USD price with full transparent breakdown.
        Shows exactly where every dollar goes before buyer pays.
        Codex Law 5: Transparency.
        """
        info       = SUPPORTED_CURRENCIES.get(currency, SUPPORTED_CURRENCIES["USD"])
        platform   = 1.00 if include_platform_fee else 0.0
        breakdown  = build_checkout_breakdown(
            product_price = usd_amount,
            platform_fee  = platform
        )
        return {
            "product_price":    f"${usd_amount:.2f}",
            "currency":         currency,
            "currency_name":    info["name"],
            "symbol":           info["symbol"],
            "breakdown":        breakdown["breakdown"],
            "total_usd":        breakdown["total_usd"],
            "processing_fee":   breakdown["processing_fee"],
            "note":             breakdown["transparency_note"],
            "currency_note":    "Exact amount in your currency calculated at checkout by Stripe."
        }

    # ── Live Gifts ────────────────────────────────────────────────────────────

    def get_gift_types(self) -> list:
        """Return available gift types. Simple, transparent, no scarcity."""
        return [
            {
                "id":        gift_id,
                "name":      info["name"],
                "emoji":     info["emoji"],
                "usd_value": info["usd_value"],
                "note":      "100% goes to the creator. The Commons takes nothing from gifts."
            }
            for gift_id, info in GIFT_TYPES.items()
        ]

    def send_gift(self, db: Session,
                  sender_id: int,
                  creator_id: int,
                  live_post_id: int,
                  gift_type: str,
                  currency: str = "USD",
                  message: str = "") -> dict:
        """
        Send a gift during a live stream.
        100% goes to the creator. Always.
        Platform takes nothing from gifts.
        """
        if gift_type not in GIFT_TYPES:
            return {"ok": False, "error": "Invalid gift type."}

        if sender_id == creator_id:
            return {"ok": False, "error": "You cannot gift yourself."}

        if currency not in SUPPORTED_CURRENCIES:
            return {"ok": False, "error": f"Currency '{currency}' not supported."}

        gift_info  = GIFT_TYPES[gift_type]
        usd_value  = gift_info["usd_value"]

        # Record the gift
        gift = LiveGift(
            live_post_id  = live_post_id,
            sender_id     = sender_id,
            creator_id    = creator_id,
            gift_type     = gift_type,
            gift_emoji    = gift_info["emoji"],
            usd_value     = usd_value,
            currency_paid = currency,
            amount_paid   = usd_value,  # Stripe handles actual conversion
            message       = message[:200] if message else "",
        )
        db.add(gift)

        # Update creator wallet
        wallet = db.query(CreatorWallet).filter(
            CreatorWallet.creator_id == creator_id
        ).first()

        if wallet:
            wallet.balance_usd  += usd_value
            wallet.total_earned += usd_value
            wallet.updated_at    = datetime.utcnow()
        else:
            db.add(CreatorWallet(
                creator_id   = creator_id,
                balance_usd  = usd_value,
                total_earned = usd_value,
            ))

        db.commit()

        breakdown = build_checkout_breakdown(gift_value=usd_value, platform_fee=0.0)
        return {
            "ok":        True,
            "gift":      gift_info["emoji"],
            "gift_name": gift_info["name"],
            "value":     f"${usd_value:.2f}",
            "message":   message,
            "breakdown": breakdown["breakdown"],
            "total":     f"${breakdown['total_usd']:.2f}",
            "note":      "100% of the gift value goes to the creator. You pay Stripe processing on top.",
            "legal_notice": FACILITATOR_DISCLAIMER,
        }

    def get_live_gifts(self, db: Session,
                       live_post_id: int) -> List[dict]:
        """Get all gifts sent during a live stream."""
        from .database import User
        gifts = (
            db.query(LiveGift)
            .filter(LiveGift.live_post_id == live_post_id)
            .order_by(LiveGift.created_at.desc())
            .limit(100)
            .all()
        )
        result = []
        for g in gifts:
            sender = db.query(User).filter(User.id == g.sender_id).first()
            result.append({
                "emoji":      g.gift_emoji,
                "gift_name":  GIFT_TYPES.get(g.gift_type, {}).get("name", g.gift_type),
                "sender":     sender.username if sender else "anonymous",
                "value":      f"${g.usd_value:.2f}",
                "message":    g.message,
                "sent_at":    g.created_at.isoformat(),
            })
        return result

    def get_creator_wallet(self, db: Session, creator_id: int) -> dict:
        """Get a creator's wallet balance."""
        wallet = db.query(CreatorWallet).filter(
            CreatorWallet.creator_id == creator_id
        ).first()

        if not wallet:
            return {
                "ok":          True,
                "balance_usd": 0.0,
                "total_earned": 0.0,
                "last_payout": None,
                "stripe_connected": False,
                "note": "Connect Stripe to receive payouts."
            }

        return {
            "ok":              True,
            "balance_usd":     wallet.balance_usd,
            "total_earned":    wallet.total_earned,
            "last_payout":     wallet.last_payout.isoformat() if wallet.last_payout else None,
            "stripe_connected": bool(wallet.stripe_account_id),
            "note":            "Connect Stripe to receive payouts of your gift earnings."
        }


payment_manager = PaymentManager()
