"""
commerce.py — The Commons Marketplace

Flat $1 transaction fee. Operating costs only. No profit.
Local small businesses and individual creators only.
No corporations. No private equity. No publicly traded companies.

The $1 fee circulates money locally — into the hands
of the people doing the actual work.

Codex Law 11: Local Commerce
Codex Law 12: No Profit

— Sovereign Human T.L. Powers · The Commons · 2026
  Power to the People
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .database import (
    Product, SellerProfile, Transaction, Order, OrderItem, User, UserRole
)
from .config import config

PLATFORM_FEE = 1.00  # Always $1. Codex Law 12. Never changes.


class Commerce:

    # ── Seller Registration ───────────────────────────────────────────────────

    def register_seller(self, db: Session, user: User,
                        business_name: str,
                        business_type: str) -> dict:
        """
        Register a seller. Individual creators and locally owned
        small businesses only. Corporations are permanently ineligible.
        """

        # Codex Law 11 enforcement
        if business_type not in ("individual", "small_business"):
            return {
                "ok": False,
                "error": (
                    "The Commons marketplace is for individual creators "
                    "and locally owned small businesses only. "
                    "Corporations are not eligible. This is Codex Law 11."
                )
            }

        existing = db.query(SellerProfile).filter(
            SellerProfile.user_id == user.id
        ).first()
        if existing:
            return {"ok": False, "error": "You already have a seller profile."}

        profile = SellerProfile(
            user_id        = user.id,
            business_name  = business_name,
            business_type  = business_type,
            is_corporation = False,      # Codex Law 11 — always False
            is_publicly_traded = False,  # Codex Law 11 — always False
            is_verified    = False,      # Pending review
        )
        db.add(profile)

        # Upgrade user role to seller
        user.role = UserRole.SELLER
        db.commit()
        db.refresh(profile)

        print(f"[COMMERCE] Seller registered: {business_name} ({business_type})")
        return {"ok": True, "profile": profile}

    def verify_seller(self, db: Session, seller_id: int,
                      reviewer: User) -> dict:
        """Circle verifies a seller meets Codex Law 11 requirements."""
        if reviewer.role.value not in ("circle", "sovereign"):
            return {"ok": False, "error": "Circle access required."}

        profile = db.query(SellerProfile).filter(
            SellerProfile.id == seller_id
        ).first()
        if not profile:
            return {"ok": False, "error": "Seller profile not found."}

        # Final Codex Law 11 check before verification
        if profile.is_corporation or profile.is_publicly_traded:
            return {
                "ok": False,
                "error": "Cannot verify: this seller violates Codex Law 11."
            }

        profile.is_verified  = True
        profile.approved_at  = datetime.utcnow()
        db.commit()

        print(f"[COMMERCE] Seller {seller_id} verified by {reviewer.username}.")
        return {"ok": True}

    # ── Products ──────────────────────────────────────────────────────────────

    def create_product(self, db: Session, user: User,
                       name: str, description: str,
                       price: float, media_path: str = "") -> dict:
        """Create a product listing."""

        profile = db.query(SellerProfile).filter(
            SellerProfile.user_id == user.id
        ).first()
        if not profile:
            return {"ok": False, "error": "You need a seller profile first."}
        if not profile.is_verified:
            return {"ok": False, "error": "Your seller profile is pending verification."}

        if price <= 0:
            return {"ok": False, "error": "Price must be greater than $0."}
        if price > 10000:
            return {"ok": False, "error": "Maximum product price is $10,000."}
        if not name or len(name) > 300:
            return {"ok": False, "error": "Product name must be 1-300 characters."}

        product = Product(
            seller_id   = profile.id,
            name        = name,
            description = description,
            price       = price,
            media_path  = media_path,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        print(f"[COMMERCE] Product listed: {name} (${price:.2f})")
        return {"ok": True, "product": product}

    def get_marketplace(self, db: Session,
                        limit: int = 40,
                        offset: int = 0,
                        category: str = None) -> List[Product]:
        """
        Get marketplace listings.
        Organized by community value — not by who paid for placement.
        Every seller gets the same visibility.
        The feed is never for sale.
        """
        query = (
            db.query(Product)
            .filter(Product.is_active == True)
            .join(SellerProfile)
            .filter(SellerProfile.is_verified == True)
            .order_by(
                desc(Product.community_score),
                desc(Product.created_at)
            )
        )
        return query.offset(offset).limit(limit).all()

    def get_product(self, db: Session, product_id: int) -> Optional[Product]:
        return db.query(Product).filter(
            Product.id == product_id,
            Product.is_active == True
        ).first()

    # ── Transactions ──────────────────────────────────────────────────────────

    def initiate_purchase(self, db: Session, buyer: User,
                          product_ids: list) -> dict:
        """
        Initiate a purchase — one order, one $1 fee.
        No matter how many items. Always $1 per sale. Codex Law 12.

        product_ids: list of product IDs being purchased in this order.
        One checkout = one $1 fee. Never per item.
        """
        if not product_ids:
            return {"ok": False, "error": "No products selected."}

        items_data = []
        items_total = 0.0

        for product_id in product_ids:
            product = self.get_product(db, product_id)
            if not product:
                return {"ok": False, "error": f"Product {product_id} not found."}

            # Buyers cannot buy their own products
            seller = db.query(SellerProfile).filter(
                SellerProfile.id == product.seller_id
            ).first()
            if seller and seller.user_id == buyer.id:
                return {"ok": False, "error": f"You cannot purchase your own product: {product.name}"}

            items_data.append(product)
            items_total += product.price

        # One $1 fee for the entire order — never per item
        order_total = items_total + PLATFORM_FEE

        order = Order(
            buyer_id     = buyer.id,
            platform_fee = PLATFORM_FEE,   # Always $1. One per order. Always.
            items_total  = items_total,
            order_total  = order_total,
            status       = "pending",
        )
        db.add(order)
        db.flush()  # Get order.id before adding items

        for product in items_data:
            item = OrderItem(
                order_id   = order.id,
                product_id = product.id,
                quantity   = 1,
                item_price = product.price,
                line_total = product.price,
            )
            db.add(item)

        db.commit()
        db.refresh(order)

        item_summary = [f"{p.name} (${p.price:.2f})" for p in items_data]
        print(f"[COMMERCE] Order {order.id} created by {buyer.username} — "
              f"{len(items_data)} item(s), ${items_total:.2f} + $1.00 fee = ${order_total:.2f}")

        return {
            "ok":    True,
            "order": order,
            "breakdown": {
                "items":        item_summary,
                "items_total":  items_total,
                "platform_fee": PLATFORM_FEE,
                "fee_note":     "$1 flat fee per sale — not per item. Codex Law 12.",
                "order_total":  order_total,
            }
        }

    def complete_order(self, db: Session, order_id: int) -> dict:
        """Mark an order as complete."""
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"ok": False, "error": "Order not found."}
        if order.status != "pending":
            return {"ok": False, "error": f"Order is already {order.status}."}

        order.status = "completed"
        db.commit()

        print(f"[COMMERCE] Order {order_id} completed.")
        return {"ok": True, "order_id": order_id}

    # ── Stats ─────────────────────────────────────────────────────────────────

    def platform_stats(self, db: Session) -> dict:
        """
        Platform financial transparency.
        Total fees collected. All operating costs only.
        No profit. Ever.
        """
        from sqlalchemy import func
        total_orders = db.query(Order).filter(
            Order.status == "completed"
        ).count()

        total_fees = db.query(func.sum(Order.platform_fee)).filter(
            Order.status == "completed"
        ).scalar() or 0.0

        total_commerce = db.query(func.sum(Order.items_total)).filter(
            Order.status == "completed"
        ).scalar() or 0.0

        return {
            "total_orders":         total_orders,
            "total_fees_collected": f"${total_fees:.2f}",
            "total_commerce_value": f"${total_commerce:.2f}",
            "fee_per_sale":         f"${PLATFORM_FEE:.2f}",
            "fee_note":             "$1 flat fee per sale — not per item. Codex Law 12.",
            "profit":               "$0.00 — Codex Law 12",
            "note": (
                "All fees collected cover operating costs only. "
                "Any surplus is reinvested into the platform. "
                "No profit is ever distributed to anyone."
            )
        }


commerce = Commerce()
