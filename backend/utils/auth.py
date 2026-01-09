"""
Authentication utilities for JWT token verification
"""
import os
from functools import wraps
from flask import request, jsonify
import jwt


def verify_token(token):
    """Verify JWT token from Firebase Auth"""
    try:
        # In a real app, we would use firebase_admin.auth.verify_id_token(token)
        # For now, we'll use a simple JWT decode if a secret is provided,
        # or just return the user_id if in development
        if os.environ.get('FLASK_ENV') == 'development':
            # In dev, we might accept a mock token or just decode without
            # verification
            return jwt.decode(token, options={"verify_signature": False})

        # In production, this should be properly implemented with Firebase
        # Admin SDK
        # decoded_token = auth.verify_id_token(token)
        # return decoded_token
        return jwt.decode(
            token, os.environ.get('JWT_SECRET', 'dev-secret'),
            algorithms=['HS256']
        )
    except Exception:
        return None


def auth_required(f):
    """Decorator to require authentication for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No token provided'}), 401

        token = auth_header.split(' ')[1]
        decoded_token = verify_token(token)

        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401

        # Add user_id to request context
        # Support multiple common UID keys
        request.user_id = (
            decoded_token.get('uid') or
            decoded_token.get('user_id') or
            decoded_token.get('sub')
        )

        if not request.user_id:
            return jsonify({'error': 'User ID not found in token'}), 401

        return f(*args, **kwargs)

    return decorated_function
