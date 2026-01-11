import os
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
import logging


def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Try to get credentials from environment variable (JSON string)
        cred_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")

        if cred_json:
            import json

            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(
                cred, {"storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")}
            )
            logging.info("Firebase initialized with service account from environment")
        else:
            # Fallback to default credentials (works on Cloud Run)
            try:
                firebase_admin.initialize_app(
                    options={"storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")}
                )
                logging.info("Firebase initialized with default credentials")
            except Exception as e:
                logging.error(f"Failed to initialize Firebase: {e}")
                logging.warning("App will continue without Firebase. Firestore operations will fail.")
                # Do not raise here to allow app to start for local debugging

    try:
        return firestore.client(), storage.bucket(), auth
    except Exception:
        return None, None, None


# Global clients
db = None
bucket = None
auth_client = None


def get_firebase():
    global db, bucket, auth_client
    if db is None or bucket is None or auth_client is None:
        db, bucket, auth_client = init_firebase()
    return db, bucket, auth_client
