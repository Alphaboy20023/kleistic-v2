# firebase_config.py
import os
import json
import firebase_admin
from firebase_admin import credentials

def init_firebase():
    if not firebase_admin._apps:
        firebase_creds = os.getenv('FIREBASE_CREDS_JSON')

        if not firebase_creds:
            raise Exception("FIREBASE_CREDS_JSON is not set")

        try:
            
            if isinstance(firebase_creds, str):
                cred_dict = json.loads(firebase_creds)  # Turn JSON string into dict
            else:
                cred_dict = firebase_creds  

            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)

        except json.JSONDecodeError as e:
            print("🔥 JSON Decode Error in Firebase creds:", str(e))
            raise

        except Exception as e:
            print("🔥 Firebase init error:", str(e))
            raise
