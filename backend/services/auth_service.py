import logging
from datetime import datetime
from firebase_config import get_firebase

db, _, auth = get_firebase()

class AuthService:
    @staticmethod
    def register_user(email, password, role='user'):
        """Register a new user in Firebase Auth and Firestore"""
        try:
            # 1. Create user in Firebase Auth
            user_record = auth.create_user(
                email=email,
                password=password
            )
            uid = user_record.uid

            # 2. Create user profile in Firestore
            user_data = {
                'uid': uid,
                'email': email,
                'role': role,
                'created_at': datetime.utcnow(),
                'total_tokens_used': 0
            }
            db.collection('users').document(uid).set(user_data)
            
            # 3. Set custom claims for role-based access
            auth.set_custom_user_claims(uid, {'role': role})
            
            logging.info(f"User registered successfully: {email} with role {role}")
            return user_data
        except Exception as e:
            logging.error(f"Error registering user: {e}")
            raise e

    @staticmethod
    def get_user_profile(uid):
        """Get user profile from Firestore"""
        try:
            doc = db.collection('users').document(uid).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            logging.error(f"Error getting user profile: {e}")
            return None

    @staticmethod
    def update_password(uid, new_password):
        """Update user password in Firebase Auth"""
        try:
            auth.update_user(uid, password=new_password)
            logging.info(f"Password updated for user: {uid}")
            return True
        except Exception as e:
            logging.error(f"Error updating password: {e}")
            raise e

    @staticmethod
    def set_user_role(uid, role):
        """Update user role in Firestore and Firebase Auth custom claims"""
        try:
            # Update Firestore
            db.collection('users').document(uid).update({'role': role})
            # Update Auth claims
            auth.set_custom_user_claims(uid, {'role': role})
            logging.info(f"Role updated for user {uid} to {role}")
            return True
        except Exception as e:
            logging.error(f"Error setting user role: {e}")
            raise e

    @staticmethod
    def delete_user(uid):
        """Delete user from Firebase Auth and Firestore"""
        try:
            auth.delete_user(uid)
            db.collection('users').document(uid).delete()
            logging.info(f"User deleted: {uid}")
            return True
        except Exception as e:
            logging.error(f"Error deleting user: {e}")
            raise e

    @staticmethod
    def list_users():
        """List all users from Firestore"""
        try:
            users_ref = db.collection('users')
            docs = users_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logging.error(f"Error listing users: {e}")
            return []

    @staticmethod
    def verify_token(id_token):
        """Verify Firebase ID token and return decoded claims"""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logging.error(f"Error verifying token: {e}")
            return None
