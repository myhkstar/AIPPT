import os
import firebase_admin
from firebase_admin import credentials, firestore, storage, auth
import logging


def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Try to get credentials from environment variable (JSON string)
        cred_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
        
        # Log environment status (don't log the actual key)
        logging.info(f"FIREBASE_SERVICE_ACCOUNT present: {bool(cred_json)}")
        logging.info(f"GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")
        logging.info(f"FIREBASE_STORAGE_BUCKET: {os.getenv('FIREBASE_STORAGE_BUCKET')}")

        storage_bucket = os.getenv("FIREBASE_STORAGE_BUCKET")
        if not storage_bucket:
            logging.error("FIREBASE_STORAGE_BUCKET environment variable is missing!")
            raise ValueError("Storage bucket name not specified in environment variables")
            
        logging.info(f"Using Storage Bucket: {storage_bucket}")

        if cred_json:
            try:
                import json
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(
                    cred, {"storageBucket": storage_bucket}
                )
                logging.info("Firebase initialized with service account from environment")
            except Exception as e:
                logging.error(f"Failed to initialize with FIREBASE_SERVICE_ACCOUNT: {e}", exc_info=True)
                raise e
        else:
            # Fallback to default credentials (works on Cloud Run)
            try:
                logging.info("Attempting to initialize with Default Credentials (ADC)...")
                firebase_admin.initialize_app(
                    options={"storageBucket": storage_bucket}
                )
                logging.info("Firebase initialized with default credentials")
            except Exception as e:
                logging.error(f"Failed to initialize Firebase with ADC: {e}", exc_info=True)
                # We must raise here because the app cannot function without Firestore
                raise e

    try:
        return firestore.client(), storage.bucket(), auth
    except Exception as e:
        logging.error(f"Failed to get Firestore/Storage clients: {e}", exc_info=True)
        raise e


# Global clients
db = None
bucket = None
auth_client = None


def get_firebase():
    global db, bucket, auth_client
    if db is None or bucket is None or auth_client is None:
        db, bucket, auth_client = init_firebase()
    return db, bucket, auth_client
