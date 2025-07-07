import os
import json
from firebase_admin import credentials, initialize_app

def init_firebase():
    if not len(initialize_app._apps):
        firebase_creds = os.getenv("FIREBASE_CREDS_JSON")
        try:
            cred_dict = json.loads(firebase_creds)  
            cred = credentials.Certificate(cred_dict)  
            initialize_app(cred)
            print("✅ Firebase initialized successfully")
        except json.JSONDecodeError as e:
            print("🔥 JSON Decode Error in Firebase creds:", e)
        except Exception as e:
            print("🔥 Firebase init error:", e)
