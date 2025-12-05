# routes/products.py
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from dataclasses import asdict

from utilities.db import SessionLocal
from models.product import Product
from utilities.auth_utils import login_required

products_bp = Blueprint("products", __name__)


@products_bp.get("/products")
def get_products():
    with SessionLocal() as db:
        result = db.execute(text("SELECT * FROM product")).fetchall()
        products = [Product.from_row(row) for row in result]

    return jsonify([asdict(p) for p in products]), 200


@products_bp.get("/products/<int:product_id>")
def get_product(product_id: int):
    with SessionLocal() as db:
        row = db.execute(
            text("SELECT * FROM product WHERE id = :id"),
            {"id": product_id},
        ).fetchone()

        if not row:
            return jsonify({"message": f"No product found with id {product_id}."}), 404

        product = Product.from_row(row)

    return jsonify(asdict(product)), 200


@products_bp.post("/products")
@login_required
def create_product():
    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")
    currency = data.get("currency")
    vat = data.get("vat")

    if not name or price is None or stock is None or currency is None or vat is None:
        return jsonify({
            "message": "Please provide all required fields: name, price, stock, currency, vat"
        }), 400

    with SessionLocal() as db:
        db.execute(
            text("""
                INSERT INTO product (name, price, stock, currency, vat)
                VALUES (:name, :price, :stock, :currency, :vat)
            """),
            {
                "name": name,
                "price": price,
                "stock": stock,
                "currency": currency,
                "vat": vat,
            },
        )
        db.commit()

    return jsonify({"message": f"Product '{name}' was created successfully."}), 201


@products_bp.delete("/products/<int:product_id>")
@login_required
def delete_product(product_id: int):
    with SessionLocal() as db:
        db.execute(
            text("DELETE FROM product WHERE id = :id"),
            {"id": product_id},
        )
        db.commit()

    return jsonify({"message": f"Product with id {product_id} was deleted."}), 200
