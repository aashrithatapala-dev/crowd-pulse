"""
Firebase Admin SDK — used only by the YOLO detector service.
Writes crowd data to Realtime Database (/latest + /readings).
"""
import json
import os
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, db

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_PATHS = [
    os.path.join(_BASE_DIR, "firebase_key.json"),
    os.path.join(_BASE_DIR, "..", "firebase_key.json"),
]
KEY_PATH = os.environ.get("FIREBASE_KEY_PATH", next(
    (p for p in _DEFAULT_PATHS if os.path.exists(p)),
    _DEFAULT_PATHS[0],
))

DATABASE_URL = os.environ.get(
    "FIREBASE_DATABASE_URL",
    "https://godavaripro-e7aa5-default-rtdb.firebaseio.com/",
)

_initialized = False


def _load_credentials():
    cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        return credentials.Certificate(json.loads(cred_json))

    if os.path.exists(KEY_PATH):
        return credentials.Certificate(KEY_PATH)

    return None


def init_firebase():
    global _initialized
    if _initialized:
        return True

    cred = _load_credentials()
    if cred is None:
        print(f"ERROR: Firebase key not found at: {KEY_PATH}")
        print("Set FIREBASE_CREDENTIALS_JSON env var or place firebase_key.json in detector/")
        return False

    try:
        firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})
        _initialized = True
        print("Firebase connected — detector will push live data.")
        return True
    except Exception as e:
        print(f"Firebase init error: {e}")
        return False


def push_to_firebase(data):
    """Write to /latest and append to /readings/{date}/{time}."""
    if not _initialized:
        return False

    try:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S")

        record = {
            "ghat": data.get("ghat", "Ghat-1"),
            "entered": data.get("entered", 0),
            "exited": data.get("exited", 0),
            "current": data.get("current", 0),
            "detected": data.get("detected", 0),
            "status": data.get("status", "No Data"),
            "timestamp": data.get("timestamp", now.strftime("%H:%M:%S")),
            "date": date_str,
        }

        db.reference("/latest").set(record)
        db.reference(f"/readings/{date_str}/{time_str}").set(record)
        return True
    except Exception as e:
        print(f"Firebase push error: {e}")
        return False
