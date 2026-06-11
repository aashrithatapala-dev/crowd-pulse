"""
Test the full pipeline without YOLO.
Pushes fake crowd data directly to Firebase every 3 seconds.
"""
import random
import time
from datetime import datetime

from firebase_config import init_firebase, push_to_firebase

MAX_CAPACITY = 50
entered = 0
exited = 0

if not init_firebase():
    raise SystemExit("Firebase not connected. Add firebase_key.json to detector/")

print("Simulator running — pushing to Firebase every 3 seconds.")
print("Open your Netlify dashboard to see live updates.")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        entered += random.randint(0, 4)
        exited += random.randint(0, 2)
        current = max(entered - exited, 0)
        detected = random.randint(max(0, current - 3), current + 3)
        status = "OVERCROWDED" if current > MAX_CAPACITY else "SAFE"

        data = {
            "ghat": "Ghat-1",
            "entered": entered,
            "exited": exited,
            "current": current,
            "detected": detected,
            "status": status,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

        if push_to_firebase(data):
            print(f"[{data['timestamp']}] entered={entered} exited={exited} current={current} {status}")
        else:
            print("Firebase push failed")

        time.sleep(3)

except KeyboardInterrupt:
    print("\nSimulator stopped.")
