from flask import Flask, jsonify, request, session
from sqlalchemy import create_engine, URL, text
from sqlalchemy.orm import sessionmaker
from functools import wraps

url = URL.create(
    drivername="postgresql+psycopg2",
    host="localhost",
    port=5432,
    username="postgres",
    password="postgres",
    database="sparky_shop"
)

engine = create_engine(url)

app = Flask(__name__)
app.config["SECRET_KEY"] = "byt-ut-den-här-i-produktion"  # behövs för sessions
Session = sessionmaker(bind=engine)


# --- Hjälp-funktion

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"message": "Authentication required."}), 401
        return f(*args, **kwargs)
    return wrapper


# --- Users ---

@app.get('/users')
@login_required
def get_users():
    with Session() as db:
        result = db.execute(text("SELECT * FROM users")).fetchall()
        users_list = [
            {
                "id": row.id,
                "name": row.name,
                "email": row.email
            } for row in result
        ]

    return jsonify(users_list), 200

@app.post('/users')
def create_user():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"message": "Please provide name, email and password."}), 400

    with Session() as db:
        # Kolla om e-post redan finns
        existing = db.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()

        if existing:
            return jsonify({"message": "Email already registered."}), 409

        # Skapa användare (plaintext password – byt till hashing senare!)
        db.execute(
            text("""
                INSERT INTO users (name, email, password)
                VALUES (:name, :email, :password)
            """),
            {"name": name, "email": email, "password": password}
        )
        db.commit()

        # Hämta nya användaren
        new_user = db.execute(
            text("SELECT id, name, email FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()

    return jsonify({
        "message": "User created successfully.",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email
        }
    }), 201

# --- Products ---

@app.get('/products')
def get_products():
    with Session() as db:
        result = db.execute(text("SELECT * FROM product")).fetchall()
        products_list = [
            {
                "id": row.id,
                "name": row.name,
                "price": row.price,
                "stock": row.stock
            } for row in result
        ]

    return jsonify(products_list), 200


@app.get('/products/<int:product_id>')
def get_product(product_id):
    with Session() as db:
        result = db.execute(
            text("SELECT * FROM product WHERE id = :id"),
            {"id": product_id}
        ).fetchone()

        if not result:
            return jsonify({"message": f"No product found with id {product_id}."}), 404

        product = {
            "id": result.id,
            "name": result.name,
            "price": result.price,
            "stock": result.stock
        }

    return jsonify(product), 200


@app.post('/products')
@login_required
def create_product():
    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")

    if not name or price is None or stock is None:
        return jsonify({"message": "Please provide all required fields: name, price, stock."}), 400

    with Session() as db:
        db.execute(
            text("""
                INSERT INTO product (name, price, stock)
                VALUES (:name, :price, :stock)
            """),
            {"name": name, "price": price, "stock": stock}
        )
        db.commit()

    return jsonify({"message": f"Product '{name}' was created successfully."}), 201


@app.delete('/products/<int:product_id>')
@login_required
def delete_product(product_id):
    with Session() as db:
        db.execute(
            text("DELETE FROM product WHERE id = :id"),
            {"id": product_id}
        )
        db.commit()

    return jsonify({"message": f"Product with id {product_id} was deleted."}), 200


# --- LOGIN: POST / GET / DELETE på /login ---

@app.post('/login')
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"message": "Please provide email and password."}), 400

    with Session() as db:
        user = db.execute(
            text("SELECT id, name, email, password FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()

        # OBS: plaintextlösenord bara för demo.
        if not user or user.password != password:
            return jsonify({"message": "Invalid email or password."}), 401

    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_email"] = user.email

    return jsonify({
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        }
    }), 200


@app.get('/login')
def get_login():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"message": "No user is logged in."}), 401

    with Session() as db:
        user = db.execute(
            text("SELECT id, name, email FROM users WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not user:
            # Rensa session om användaren inte längre finns
            session.clear()
            return jsonify({"message": "User not found."}), 401

    return jsonify({
        "id": user.id,
        "name": user.name,
        "email": user.email
    }), 200


@app.delete('/login')
def logout():
    session.clear()
    return jsonify({"message": "Logged out."}), 200


# --- SHOPPING CART: kräver inloggad användare ---

@app.get('/cart')
@login_required
def get_cart():
    user_id = session["user_id"]

    with Session() as db:
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
            {"user_id": user_id}
        ).fetchall()

        cart_items = [
            {
                "id": row.id,
                "product_id": row.product_id,
                "product_name": row.product_name,
                "price": float(row.price) if row.price is not None else None,
                "stock": row.stock,
                "amount": row.amount,
                "total_price": float(row.price) * row.amount if row.price is not None else None
            }
            for row in result
        ]

    return jsonify(cart_items), 200


@app.post('/cart')
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

    with Session() as db:
        # Kolla att produkten finns
        product = db.execute(
            text("SELECT id FROM product WHERE id = :id"),
            {"id": product_id}
        ).fetchone()
        if not product:
            return jsonify({"message": f"No product found with id {product_id}."}), 404

        # Kolla om det redan finns en rad i cart
        row = db.execute(
            text("""
                SELECT id, amount
                FROM shopping_cart
                WHERE user_id = :user_id AND product_id = :product_id
            """),
            {"user_id": user_id, "product_id": product_id}
        ).fetchone()

        if row:
            new_amount = row.amount + amount
            db.execute(
                text("""
                    UPDATE shopping_cart
                    SET amount = :amount
                    WHERE id = :id
                """),
                {"amount": new_amount, "id": row.id}
            )
        else:
            db.execute(
                text("""
                    INSERT INTO shopping_cart (user_id, product_id, amount)
                    VALUES (:user_id, :product_id, :amount)
                """),
                {"user_id": user_id, "product_id": product_id, "amount": amount}
            )

        db.commit()

    return jsonify({"message": "Cart updated."}), 200


@app.delete('/cart')
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

    with Session() as db:
        row = db.execute(
            text("""
                SELECT id, amount
                FROM shopping_cart
                WHERE user_id = :user_id AND product_id = :product_id
            """),
            {"user_id": user_id, "product_id": product_id}
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
                {"amount": new_amount, "id": row.id}
            )
        else:
            db.execute(
                text("DELETE FROM shopping_cart WHERE id = :id"),
                {"id": row.id}
            )

        db.commit()

    return jsonify({"message": "Cart updated."}), 200


if __name__ == "__main__":
    app.run(debug=True)
