from flask import Blueprint, request, jsonify
import database

api_bp = Blueprint("api", __name__, url_prefix="/api")

# --- CUSTOMER ENDPOINTS ---

@api_bp.route("/menu", methods=["GET"])
def get_menu():
    category = request.args.get("category")
    items = database.fetch_menu(category)
    return jsonify(items), 200

@api_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = database.fetch_categories()
    return jsonify(categories), 200

@api_bp.route("/orders", methods=["POST"])
def place_order():
    data = request.get_json() or {}
    user_id = data.get("user_id", 1)
    address = data.get("address")
    items = data.get("items", [])

    if not address or not items:
        return jsonify({"error": "Delivery address and order items are required"}), 400

    try:
        order_id = database.place_order_transaction(user_id, address, items)
        return jsonify({
            "message": "Order placed successfully",
            "order_id": order_id
        }), 201
    except Exception as e:
        return jsonify({"error": f"Failed to place order: {str(e)}"}), 500

@api_bp.route("/orders/<int:order_id>", methods=["GET"])
def track_order(order_id):
    order = database.fetch_order_by_id(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order), 200


# --- ADMIN & KITCHEN ENDPOINTS ---

@api_bp.route("/admin/orders", methods=["GET"])
def get_admin_orders():
    status = request.args.get("status")
    orders = database.fetch_admin_orders(status)
    return jsonify(orders), 200

@api_bp.route("/admin/orders/status", methods=["PUT"])
def update_order_status():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    status = data.get("status")

    valid_statuses = ["Pending", "Preparing", "Out for Delivery", "Delivered", "Cancelled"]
    if not order_id or status not in valid_statuses:
        return jsonify({"error": "Valid order_id and status are required"}), 400

    database.update_order_status_db(order_id, status)
    return jsonify({"message": f"Order status updated to {status}"}), 200

@api_bp.route("/admin/menu", methods=["POST"])
def add_menu_item():
    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    category_id = data.get("category_id")
    description = data.get("description", "")

    if not name or price is None or not category_id:
        return jsonify({"error": "Name, price, and category_id are required"}), 400

    try:
        item_id = database.insert_menu_item(name, float(price), int(category_id), description)
        return jsonify({
            "message": "Menu item added successfully",
            "item_id": item_id
        }), 201
    except Exception as e:
        return jsonify({"error": f"Failed to add menu item: {str(e)}"}), 500

@api_bp.route("/admin/menu/<int:item_id>/availability", methods=["PUT"])
def update_item_stock(item_id):
    data = request.get_json() or {}
    is_available = data.get("is_available")
    if is_available is None:
        return jsonify({"error": "is_available boolean field is required"}), 400

    database.set_item_availability(item_id, bool(is_available))
    return jsonify({"message": "Availability updated successfully"}), 200

@api_bp.route("/admin/analytics", methods=["GET"])
def get_analytics_data():
    analytics = database.fetch_analytics()
    return jsonify(analytics), 200
