from flask import Blueprint, request, jsonify
from backend.models.payment import PaymentModel

payment_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

@payment_bp.route("/upi/initiate", methods=["POST"])
def initiate_upi():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    upi_id = data.get("upi_id", "user@upi")
    amount = data.get("amount")

    if not order_id or amount is None:
        return jsonify({"error": "order_id and amount are required"}), 400

    payment_info = PaymentModel.initiate_upi_payment(order_id, upi_id, float(amount))
    return jsonify({
        "message": "UPI payment transaction initiated",
        "payment": payment_info
    }), 200

@payment_bp.route("/verify", methods=["POST"])
def verify_payment():
    data = request.get_json() or {}
    order_id = data.get("order_id")
    transaction_id = data.get("transaction_id")
    status = data.get("status", "Completed")

    if not order_id or not transaction_id:
        return jsonify({"error": "order_id and transaction_id are required"}), 400

    PaymentModel.verify_payment(order_id, transaction_id, status)
    return jsonify({
        "message": "Payment verified successfully",
        "order_id": order_id,
        "transaction_id": transaction_id,
        "payment_status": status
    }), 200
