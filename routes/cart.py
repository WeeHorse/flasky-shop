# routes/cart.py
from flask import Blueprint, jsonify, request, session
from sqlalchemy import text
from dataclasses import asdict

from utilities.db import SessionLocal
from models.cart import CartItem
from utilities.auth_utils import login_required

cart_bp = Blueprint("cart", __name__)


@cart_bp.get("/cart")
@login_required
def get_cart():
    user_id = session["user_id"]

    with SessionLocal() as db:
        result = db.execute(
            text("""
                SELECT
                    sc.id,
                    sc.amount,
                    p.id   AS product_id,
                    p.name AS product_name,
                    p.price,
                    p.stock
                FROM shopping_cart sc
                JOIN product p ON sc.product_id = p.id
                WHERE sc.user_id = :user_id
            """),
            {"user_id": user_id},
        ).fetchall()

        cart_items = [CartItem.from_row(row) for row in result]

    return jsonify([asdict(ci) for ci in cart_items]), 200


@cart_bp.post("/cart")
@login_required
def add_to_cart():
    data = request.get_json() or {}
    product_id = data.get("product_id")
    amount = data.get("amount", 1)

    if not product_id:
        return jsonify({"message": "Please provide product_id."}), 400

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return jsonify({"message": "Amount must be an integer."}), 400

    if amount <= 0:
        return jsonify({"message": "Amount must be greater than 0."}), 400

    user_id = session["user_id"]

    with SessionLocal() as db:
        product = db.execute(
            text("SELECT id FROM product WHERE id = :id"),
            {"id": product_id},
        ).fetchone()

        if not product:
            return jsonify({"message": f"No product found with id {product_id}."}), 404

        row = db.execute(
            text("""
                SELECT id, amount
                FROM shopping_cart
                WHERE user_id = :user_id AND product_id = :product_id
            """),
            {"user_id": user_id, "product_id": product_id},
        ).fetchone()

        if row:
            new_amount = row.amount + amount
            db.execute(
                text("""
                    UPDATE shopping_cart
                    SET amount = :amount
                    WHERE id = :id
                """),
                {"amount": new_amount, "id": row.id},
            )
        else:
            db.execute(
                text("""
                    INSERT INTO shopping_cart (user_id, product_id, amount)
                    VALUES (:user_id, :product_id, :amount)
                """),
                {"user_id": user_id, "product_id": product_id, "amount": amount},
            )

        db.commit()

    return jsonify({"message": "Cart updated."}), 200


@cart_bp.delete("/cart")
@login_required
def remove_from_cart():
    data = request.get_json() or {}
    product_id = data.get("product_id")
    amount = data.get("amount", 1)

    if not product_id:
        return jsonify({"message": "Please provide product_id."}), 400

    try:
        amount = int(amount)
    except (ValueError, TypeError):
        return jsonify({"message": "Amount must be an integer."}), 400

    if amount <= 0:
        return jsonify({"message": "Amount must be greater than 0."}), 400

    user_id = session["user_id"]

    with SessionLocal() as db:
        row = db.execute(
            text("""
                SELECT id, amount
                FROM shopping_cart
                WHERE user_id = :user_id AND product_id = :product_id
            """),
            {"user_id": user_id, "product_id": product_id},
        ).fetchone()

        if not row:
            return jsonify({"message": "Product is not in cart."}), 404

        if row.amount > amount:
            new_amount = row.amount - amount
            db.execute(
                text("""
                    UPDATE shopping_cart
                    SET amount = :amount
                    WHERE id = :id
                """),
                {"amount": new_amount, "id": row.id},
            )
        else:
            db.execute(
                text("DELETE FROM shopping_cart WHERE id = :id"),
                {"id": row.id},
            )

        db.commit()

    return jsonify({"message": "Cart updated."}), 200
