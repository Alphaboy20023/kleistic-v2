import firebase_admin
from firebase_admin import credentials
import os
import json

def init_firebase():
    if not firebase_admin._apps:
        firebase_creds = os.getenv('FIREBASE_CREDS_JSON')
        if not firebase_creds:
            raise Exception("FIREBASE_CREDS_JSON is missing")
        cred = credentials.Certificate(json.loads(firebase_creds))
        firebase_admin.initialize_app(cred)
