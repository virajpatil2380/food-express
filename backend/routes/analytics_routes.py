from flask import Blueprint, jsonify
from backend.models.payment import PaymentModel

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api")

@analytics_bp.route("/admin/analytics", methods=["GET"])
def get_analytics():
    data = PaymentModel.get_analytics()
    return jsonify(data), 200
