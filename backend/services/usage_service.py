import logging
from datetime import datetime
from firebase_config import get_firebase

db, _, _ = get_firebase()

class UsageService:
    @staticmethod
    def record_usage(uid, topic, result_url, tokens_used):
        """Record PPT generation usage in Firestore"""
        try:
            # 1. Add record to usage_records collection
            record_data = {
                'uid': uid,
                'topic': topic,
                'result_url': result_url,
                'tokens_used': tokens_used,
                'timestamp': datetime.utcnow()
            }
            db.collection('usage_records').add(record_data)

            # 2. Update user's total tokens used
            user_ref = db.collection('users').document(uid)
            user_doc = user_ref.get()
            if user_doc.exists:
                current_tokens = user_doc.to_dict().get('total_tokens_used', 0)
                user_ref.update({
                    'total_tokens_used': current_tokens + tokens_used
                })
            
            logging.info(f"Usage recorded for user {uid}: {tokens_used} tokens")
            return True
        except Exception as e:
            logging.error(f"Error recording usage: {e}")
            return False

    @staticmethod
    def get_user_usage(uid):
        """Get usage records for a specific user"""
        try:
            records_ref = db.collection('usage_records').where('uid', '==', uid).order_by('timestamp', direction='DESCENDING')
            docs = records_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logging.error(f"Error getting user usage: {e}")
            return []

    @staticmethod
    def get_all_usage():
        """Get all usage records (for admin)"""
        try:
            records_ref = db.collection('usage_records').order_by('timestamp', direction='DESCENDING')
            docs = records_ref.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logging.error(f"Error getting all usage: {e}")
            return []
