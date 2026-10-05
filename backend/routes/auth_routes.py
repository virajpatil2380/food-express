from flask import Blueprint, request, jsonify
from backend.models.user import UserModel

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Staff emails — only these can access Admin/Kitchen/Delivery panels
STAFF_EMAILS = {
    "admin@foodexpress.com",
    "kitchen@foodexpress.com",
    "delivery@foodexpress.com",
}


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")

    if not name or not email or not phone or not password:
        return jsonify({"error": "Name, email, phone, and password are required"}), 400

    if email.strip().lower() in STAFF_EMAILS:
        return jsonify({"error": "This email is reserved for staff."}), 403

    user, err = UserModel.create_user(name, email.strip(), phone, password, "Customer")
    if err:
        return jsonify({"error": err}), 400

    return jsonify({"message": "Account created", "user": user}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user, err = UserModel.authenticate(email.strip(), password)
    if err:
        return jsonify({"error": err}), 401

    return jsonify({"message": "Login successful", "user": user}), 200
