# routes/auth.py
from flask import Blueprint, jsonify, request, session
from sqlalchemy import text
from dataclasses import asdict

from utilities.db import SessionLocal
from models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Please provide email and password."}), 400

    with SessionLocal() as db:
        row = db.execute(
            text("SELECT id, name, email, password FROM users WHERE email = :email"),
            {"email": email},
        ).fetchone()

        if not row or row.password != password:
            return jsonify({"message": "Invalid email or password."}), 401

    user = User(id=row.id, name=row.name, email=row.email)

    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_email"] = user.email

    return jsonify({
        "message": "Login successful.",
        "user": asdict(user),
    }), 200


@auth_bp.get("/login")
def get_login():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "No user is logged in."}), 401

    with SessionLocal() as db:
        row = db.execute(
            text("SELECT id, name, email FROM users WHERE id = :id"),
            {"id": user_id},
        ).fetchone()

        if not row:
            session.clear()
            return jsonify({"message": "User not found."}), 401

    user = User.from_row(row)

    return jsonify(asdict(user)), 200


@auth_bp.delete("/login")
def logout():
    session.clear()
    return jsonify({"message": "Logged out."}), 200
