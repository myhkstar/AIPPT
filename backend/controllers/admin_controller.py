from flask import Blueprint, request, jsonify, g
from services.auth_service import AuthService
from services.usage_service import UsageService
from utils.auth_middleware import auth_required, admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/users', methods=['GET'])
@auth_required
@admin_required
def list_users():
    """List all users"""
    users = AuthService.list_users()
    return jsonify(users), 200

@admin_bp.route('/users', methods=['POST'])
@auth_required
@admin_required
def create_user():
    """Create a new user with a specific role"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    try:
        user_data = AuthService.register_user(email, password, role)
        return jsonify({"message": "User created successfully", "user": user_data}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@admin_bp.route('/users/<uid>', methods=['DELETE'])
@auth_required
@admin_required
def delete_user(uid):
    """Delete a user"""
    try:
        AuthService.delete_user(uid)
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@admin_bp.route('/users/<uid>/role', methods=['PATCH'])
@auth_required
@admin_required
def update_user_role(uid):
    """Update a user's role"""
    data = request.get_json()
    role = data.get('role')

    if not role:
        return jsonify({"error": "Missing role"}), 400

    try:
        AuthService.set_user_role(uid, role)
        return jsonify({"message": "User role updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@admin_bp.route('/usage', methods=['GET'])
@auth_required
@admin_required
def get_all_usage():
    """View all usage records across all users"""
    usage_records = UsageService.get_all_usage()
    return jsonify(usage_records), 200
