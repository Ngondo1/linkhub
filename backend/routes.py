from flask import Blueprint, jsonify

# This Blueprint gets registered in app.py
main_bp = Blueprint("main_bp", __name__)

@main_bp.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "OK", "message": "API is working"})
