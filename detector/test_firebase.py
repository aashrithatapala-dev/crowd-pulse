"""Verify detector can read/write Firebase."""
from firebase_config import init_firebase, push_to_firebase

if not init_firebase():
    raise SystemExit(1)

ok = push_to_firebase({
    "ghat": "Ghat-1",
    "entered": 1,
    "exited": 0,
    "current": 1,
    "detected": 1,
    "status": "SAFE",
    "timestamp": "test",
})
print("OK" if ok else "FAILED")
raise SystemExit(0 if ok else 1)
