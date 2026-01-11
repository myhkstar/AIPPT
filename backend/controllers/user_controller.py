from flask import Blueprint, jsonify, g
from services.auth_service import AuthService
from services.usage_service import UsageService
from utils.auth_middleware import auth_required

user_bp = Blueprint('user', __name__, url_prefix='/api/user')

@user_bp.route('/profile', methods=['GET'])
@auth_required
def get_profile():
    """Get current user's profile and token usage summary"""
    uid = g.user['uid']
    profile = AuthService.get_user_profile(uid)
    if profile:
        return jsonify(profile), 200
    return jsonify({"error": "User profile not found"}), 404

@user_bp.route('/usage', methods=['GET'])
@auth_required
def get_usage():
    """Get current user's PPT generation history"""
    uid = g.user['uid']
    usage_records = UsageService.get_user_usage(uid)
    return jsonify(usage_records), 200
