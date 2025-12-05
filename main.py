# app.py
from flask import Flask
from routes.users import users_bp
from routes.products import products_bp
from routes.auth import auth_bp
from routes.cart import cart_bp
from routes.vats import vats_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "byt-ut-den-här-i-produktion"

    # Register routes (flask calls it blueprints..)
    app.register_blueprint(users_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(vats_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
