import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from flask import Flask, jsonify
from backend.config import Config
from backend.database import init_db

from backend.routes.auth_routes import auth_bp
from backend.routes.menu_routes import menu_bp
from backend.routes.order_routes import order_bp
from backend.routes.payment_routes import payment_bp
from backend.routes.analytics_routes import analytics_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize DB & Seed Data
    init_db()

    # Register Modular Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(analytics_bp)

    @app.route("/")
    def index():
        return jsonify({
            "service": "Food Express REST API",
            "version": "2.0",
            "status": "Online",
            "endpoints": [
                "/api/auth/login",
                "/api/auth/signup",
                "/api/menu",
                "/api/orders",
                "/api/payments/upi/initiate",
                "/api/admin/orders",
                "/api/admin/analytics"
            ]
        })

    return app

app = create_app()

if __name__ == "__main__":
    print(f"Starting Food Express API Server on http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=True)
