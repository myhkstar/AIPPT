from flask import Blueprint, request, jsonify, g
from services.auth_service import AuthService
from utils.auth_middleware import auth_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user') # Default to user

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    try:
        user_data = AuthService.register_user(email, password, role)
        return jsonify({"message": "User registered successfully", "user": user_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/change-password', methods=['POST'])
@auth_required
def change_password():
    data = request.get_json()
    new_password = data.get('new_password')
    uid = g.user['uid']

    if not new_password:
        return jsonify({"error": "Missing new password"}), 400

    try:
        AuthService.update_password(uid, new_password)
        return jsonify({"message": "Password updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@auth_bp.route('/me', methods=['GET'])
@auth_required
def get_me():
    """Get current user's profile and claims"""
    uid = g.user['uid']
    profile = AuthService.get_user_profile(uid)
    if profile:
        return jsonify(profile), 200
    return jsonify({"error": "User profile not found"}), 404
