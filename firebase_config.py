import firebase_admin
from firebase_admin import credentials
import os
import json

def init_firebase():
    if not firebase_admin._apps:  
        firebase_creds_str = os.environ.get("FIREBASE_CREDS_JSON")

        if not firebase_creds_str:
            raise ValueError("Missing FIREBASE_CREDS_JSON in environment")

       
        cred_dict = json.loads(firebase_creds_str)
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
