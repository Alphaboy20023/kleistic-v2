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
        
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

        cred = credentials.Certificate(cred_dict)

        initialize_app(cred)
        
        
# import json

# with open("kleistic-firebase-adminsdk-fbsvc-5486d3f42c.json") as f:
#     data = json.load(f)

# # Replace real newlines in the private key with \\n
# data["private_key"] = data["private_key"].replace("\n", "\\n")

# escaped = json.dumps(data)
# print(escaped)  # This is the final value you paste into FIREBASE_CREDS_JSON
