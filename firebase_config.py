import json
import os
from firebase_admin import credentials, initialize_app
import firebase_admin

def init_firebase():
    if not firebase_admin._apps:
        firebase_creds_str = os.environ.get("FIREBASE_CREDS_JSON")

        if not firebase_creds_str:
            raise ValueError("Missing FIREBASE_CREDS_JSON environment variable")

        # No replace needed here
        cred_dict = json.loads(firebase_creds_str)
        cred = credentials.Certificate(cred_dict)

        initialize_app(cred)
