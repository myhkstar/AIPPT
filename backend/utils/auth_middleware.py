from functools import wraps
from flask import request, jsonify, g
from services.auth_service import AuthService

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized", "message": "Missing or invalid token"}), 401
        
        id_token = auth_header.split('Bearer ')[1]
        decoded_token = AuthService.verify_token(id_token)
        
        if not decoded_token:
            return jsonify({"error": "Unauthorized", "message": "Invalid token"}), 401
        
        # Store user info in flask.g for access in routes
        g.user = decoded_token
        return f(*args, **kwargs)
    
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user'):
            return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
        
        role = g.user.get('role')
        if role != 'admin':
            return jsonify({"error": "Forbidden", "message": "Admin access required"}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def vip_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, 'user'):
            return jsonify({"error": "Unauthorized", "message": "Authentication required"}), 401
        
        role = g.user.get('role')
        if role not in ['vip', 'admin']:
            return jsonify({"error": "Forbidden", "message": "VIP access required"}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
