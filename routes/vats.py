# routes/vats.py
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from dataclasses import asdict

from utilities.db import SessionLocal
from models.vat import Vat
from utilities.auth_utils import login_required

vats_bp = Blueprint("vats", __name__)


@vats_bp.get("/vats")
@login_required
def get_vats():
    with SessionLocal() as db:
        result = db.execute(text("SELECT * FROM vats")).fetchall()
        vats = [Vat.from_row(row) for row in result]

    return jsonify([asdict(v) for v in vats]), 200


@vats_bp.post("/vats")
@login_required
def create_vats():
    data = request.get_json() or {}
    description = data.get("description")
    amount = data.get("amount")
    region = data.get("region")

    if not description or amount is None or not region:
        return jsonify({
            "message": "Please provide all required fields: description, amount, region."
        }), 400

    with SessionLocal() as db:
        db.execute(
            text("""
                INSERT INTO vats (description, amount, region)
                VALUES (:description, :amount, :region)
            """),
            {"description": description, "amount": amount, "region": region},
        )
        db.commit()

    return jsonify({"message": f"vats '{description}' was created successfully."}), 201


@vats_bp.put("/vats/<int:vat_id>")
@login_required
def update_vats(vat_id: int):
    data = request.get_json() or {}
    description = data.get("description")
    amount = data.get("amount")
    region = data.get("region")

    if not description or amount is None or not region:
        return jsonify({
            "message": "Please provide all required fields: description, amount, region."
        }), 400

    with SessionLocal() as db:
        db.execute(
            text("""
                UPDATE vats
                SET description = :description,
                    amount = :amount,
                    region = :region
                WHERE id = :id
            """),
            {
                "description": description,
                "amount": amount,
                "region": region,
                "id": vat_id,
            },
        )
        db.commit()

    return jsonify({"message": f"vats '{description}' was updated successfully."}), 201
