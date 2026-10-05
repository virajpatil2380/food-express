from flask import Blueprint, request, jsonify
from backend.models.menu import MenuModel

menu_bp = Blueprint("menu", __name__, url_prefix="/api")


@menu_bp.route("/menu", methods=["GET"])
def get_menu():
    category = request.args.get("category")
    items = MenuModel.get_menu(category)
    return jsonify(items), 200


@menu_bp.route("/menu/<int:item_id>", methods=["GET"])
def get_menu_item(item_id):
    item = MenuModel.get_item_by_id(item_id)
    if not item:
        return jsonify({"error": "Menu item not found"}), 404
    return jsonify(item), 200


@menu_bp.route("/categories", methods=["GET"])
def get_categories():
    categories = MenuModel.get_categories()
    return jsonify(categories), 200


@menu_bp.route("/admin/categories", methods=["POST"])
def add_category():
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Category name is required"}), 400
    cat_id = MenuModel.add_category(name)
    return jsonify({"message": "Category added", "category_id": cat_id}), 201


@menu_bp.route("/admin/menu", methods=["POST"])
def add_menu_item():
    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    category_id = data.get("category_id")
    description = data.get("description", "")
    image_url = data.get("image_url", "")

    if not name or price is None or not category_id:
        return jsonify({"error": "Name, price, and category_id are required"}), 400

    try:
        item_id = MenuModel.add_menu_item(name, float(price), int(category_id), description, image_url)
        return jsonify({"message": "Menu item added successfully", "item_id": item_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@menu_bp.route("/admin/menu/<int:item_id>", methods=["PUT"])
def update_menu_item(item_id):
    """Full update of a menu item's name, price, category, description, and image."""
    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    category_id = data.get("category_id")
    description = data.get("description", "")
    image_url = data.get("image_url", "")

    if not name or price is None or not category_id:
        return jsonify({"error": "Name, price, and category_id are required"}), 400

    try:
        success = MenuModel.update_menu_item(item_id, name, float(price), int(category_id), description, image_url)
        if success:
            return jsonify({"message": f"Menu item #{item_id} updated successfully"}), 200
        return jsonify({"error": "Item not found or no changes made"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@menu_bp.route("/admin/menu/<int:item_id>", methods=["DELETE"])
def delete_menu_item(item_id):
    """Permanently delete a menu item."""
    try:
        success = MenuModel.delete_menu_item(item_id)
        if success:
            return jsonify({"message": f"Menu item #{item_id} deleted successfully"}), 200
        return jsonify({"error": "Item not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@menu_bp.route("/admin/menu/<int:item_id>/availability", methods=["PUT"])
def toggle_availability(item_id):
    data = request.get_json() or {}
    is_available = data.get("is_available")
    if is_available is None:
        return jsonify({"error": "is_available boolean required"}), 400

    MenuModel.update_availability(item_id, bool(is_available))
    return jsonify({"message": "Availability updated successfully"}), 200
