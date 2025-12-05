# routes/users.py
from flask import Blueprint, jsonify, request
from sqlalchemy import text
from dataclasses import asdict

from utilities.db import SessionLocal
from models.user import User

users_bp = Blueprint("users", __name__)


@users_bp.get("/users")
def get_users():
    with SessionLocal() as db:
        result = db.execute(text("SELECT id, name, email FROM users")).fetchall()
        users = [User.from_row(row) for row in result]

    return jsonify([asdict(u) for u in users]), 200


@users_bp.post("/users")
def create_user():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"message": "Please provide name, email and password."}), 400

    with SessionLocal() as db:
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()

        if existing:
            return jsonify({"message": "Email already registered."}), 409

        db.execute(
            text("""
                INSERT INTO users (name, email, password)
                VALUES (:name, :email, :password)
            """),
            {"name": name, "email": email, "password": password},
        )
        db.commit()

        new_user_row = db.execute(
            text("SELECT id, name, email FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()

    new_user = User.from_row(new_user_row)

    return jsonify({
        "message": "User created successfully.",
        "user": asdict(new_user),
    }), 201
