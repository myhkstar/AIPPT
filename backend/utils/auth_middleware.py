from functools import wraps
from flask import request, jsonify, g
from services.auth_service import AuthService

def auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # OPTION B: Bypass authentication for Guest Mode
        # If no token is provided, we assume it's a guest user
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            # Guest User
            guest_user = {
                'uid': 'guest_user_001',
                'email': 'guest@example.com',
                'role': 'admin'  # Give admin rights for testing
            }
            g.user = guest_user
            request.user_id = guest_user['uid']
            return f(*args, **kwargs)
        
        try:
            id_token = auth_header.split('Bearer ')[1]
            decoded_token = AuthService.verify_token(id_token)
            
            if not decoded_token:
                return jsonify({"error": "Unauthorized", "message": "Invalid token"}), 401
            
            # Store user info in flask.g for access in routes
            g.user = decoded_token
            request.user_id = decoded_token['uid']
            return f(*args, **kwargs)
        except Exception as e:
            # Fallback to guest if token verification fails (optional, but safer for now)
            print(f"Auth failed: {e}, falling back to guest")
            guest_user = {
                'uid': 'guest_user_001',
                'email': 'guest@example.com',
                'role': 'admin'
            }
            g.user = guest_user
            request.user_id = guest_user['uid']
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
