from flask import Blueprint, request, jsonify
from backend.models.order import OrderModel

order_bp = Blueprint("orders", __name__, url_prefix="/api")

VALID_STATUSES = ["Pending", "Preparing", "Ready", "Out for Delivery", "Delivered", "Cancelled"]


@order_bp.route("/orders", methods=["POST"])
def place_order():
    data = request.get_json() or {}
    user_id = data.get("user_id", 1)
    address = data.get("address")
    items = data.get("items", [])
    payment_method = data.get("payment_method", "COD")

    if not address or not items:
        return jsonify({"error": "Delivery address and order items are required"}), 400

    try:
        order_id = OrderModel.create_order(user_id, address, items, payment_method)
        return jsonify({"message": "Order placed successfully", "order_id": order_id}), 201
    except Exception as e:
        return jsonify({"error": f"Failed to place order: {str(e)}"}), 500


@order_bp.route("/orders/<int:order_id>", methods=["GET"])
def track_order(order_id):
    order = OrderModel.get_order_by_id(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404
    return jsonify(order), 200


@order_bp.route("/orders/user/<int:user_id>", methods=["GET"])
def user_orders(user_id):
    orders = OrderModel.get_user_orders(user_id)
    return jsonify(orders), 200


@order_bp.route("/orders/<int:order_id>/rate", methods=["PUT"])
def rate_order(order_id):
    """Save customer rating & review for an order."""
    data = request.get_json() or {}
    rating = data.get("rating")
    review_text = data.get("review_text", "")

    if not rating or not (1 <= int(rating) <= 5):
        return jsonify({"error": "Valid rating between 1 and 5 is required"}), 400

    OrderModel.save_rating(order_id, int(rating), review_text.strip())
    return jsonify({"message": "Thank you for your rating & feedback!"}), 200


@order_bp.route("/admin/orders", methods=["GET"])
def get_admin_orders():
    status = request.args.get("status")
    orders = OrderModel.get_all_orders(status)
    return jsonify(orders), 200


@order_bp.route("/admin/orders/status", methods=["PUT"])
def update_status():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    status = data.get("status")

    if not order_id or status not in VALID_STATUSES:
        return jsonify({"error": "Valid order_id and status are required"}), 400

    OrderModel.update_status(order_id, status)
    return jsonify({"message": f"Order status updated to {status}"}), 200


# ── Delivery Boy Endpoints ──

@order_bp.route("/delivery/orders", methods=["GET"])
def get_delivery_orders():
    delivery_user_id = request.args.get("delivery_user_id")
    orders = OrderModel.get_delivery_orders(delivery_user_id)
    return jsonify(orders), 200


@order_bp.route("/delivery/pickup", methods=["PUT"])
def pickup_order():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    delivery_user_id = data.get("delivery_user_id")

    if not order_id or not delivery_user_id:
        return jsonify({"error": "order_id and delivery_user_id required"}), 400

    OrderModel.assign_delivery(order_id, delivery_user_id)
    return jsonify({"message": f"Order #{order_id} picked up for delivery"}), 200


@order_bp.route("/delivery/delivered", methods=["PUT"])
def mark_delivered():
    data = request.get_json() or {}
    order_id = data.get("order_id")

    if not order_id:
        return jsonify({"error": "order_id required"}), 400

    OrderModel.update_status(order_id, "Delivered")
    return jsonify({"message": f"Order #{order_id} delivered successfully"}), 200
