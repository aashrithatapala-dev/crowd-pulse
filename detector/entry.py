"""
GodavariPro YOLO Detector Service
Continuously monitors a video stream, counts people, and pushes live data to Firebase.
Runs 24/7 on Railway, Render, a VPS, or a local machine.

No Flask. No dashboard. Firebase is the only data sink.
"""
import math
import os
import time
from datetime import datetime

import cv2
import yt_dlp
from ultralytics import YOLO

from firebase_config import init_firebase, push_to_firebase

# ── Config (override via environment variables) ──────────────
YOUTUBE_URL = os.environ.get(
    "YOUTUBE_URL",
    "https://youtu.be/O7iV4kO8z6I?si=F4M6XmOx1vz7odpv",
)
MAX_CAPACITY = int(os.environ.get("MAX_CAPACITY", "50"))
PROCESS_INTERVAL = float(os.environ.get("PROCESS_INTERVAL", "2"))
HEADLESS = os.environ.get("HEADLESS", "1") == "1"
GHAT_NAME = os.environ.get("GHAT_NAME", "Ghat-1")

# ── State ──────────────────────────────────────────────────────
model = YOLO("yolov8n.pt")
line_y = int(480 * 0.8)
people = {}
person_id = 0
entered = 0
exited = 0
last_process_time = 0
display_frame = None


def get_stream_url(url):
    ydl_opts = {"format": "best"}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info["url"]


def distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def show_frame(frame):
    if not HEADLESS:
        cv2.imshow("Crowd Monitor", frame)


def publish(data):
    if push_to_firebase(data):
        print(f"[FIREBASE] {data}")
    else:
        print(f"[ERROR] Firebase push failed: {data}")


def run_stream():
    global people, person_id, entered, exited, last_process_time, display_frame

    print("Connecting to stream...")
    video_url = get_stream_url(YOUTUBE_URL)
    cap = cv2.VideoCapture(video_url)

    if not cap.isOpened():
        print("ERROR: Could not open stream.")
        return True

    print("Stream connected. Detection running...")
    last_process_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Stream ended or dropped. Reconnecting...")
            cap.release()
            return True

        frame = cv2.resize(frame, (640, 480))
        current_time = time.time()

        if current_time - last_process_time < PROCESS_INTERVAL:
            cv2.line(frame, (0, line_y), (640, line_y), (255, 0, 0), 2)
            show_frame(display_frame if display_frame is not None else frame)
        else:
            results = model(frame)
            new_people = {}

            for r in results:
                boxes = r.boxes.xyxy.cpu().numpy()
                classes = r.boxes.cls.cpu().numpy()

                for box, cls in zip(boxes, classes):
                    if int(cls) != 0:
                        continue

                    x1, y1, x2, y2 = map(int, box)
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    matched = False
                    color = (0, 255, 0)

                    for pid, (px, py, counted) in people.items():
                        if distance((cx, cy), (px, py)) < 40:
                            new_people[pid] = (cx, cy, counted)

                            if not counted:
                                if py > line_y and cy <= line_y:
                                    entered += 1
                                    new_people[pid] = (cx, cy, True)
                                elif py < line_y and cy >= line_y:
                                    exited += 1
                                    new_people[pid] = (cx, cy, True)
                                    color = (0, 0, 255)

                            matched = True
                            break

                    if not matched:
                        new_people[person_id] = (cx, cy, False)
                        person_id += 1

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            people = new_people
            current_people = len(new_people)
            status = "OVERCROWDED" if current_people > MAX_CAPACITY else "SAFE"
            s_color = (0, 0, 255) if status == "OVERCROWDED" else (0, 255, 0)

            cv2.line(frame, (0, line_y), (640, line_y), (255, 0, 0), 2)
            cv2.putText(frame, f"Entered: {entered}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(frame, f"Exited: {exited}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(frame, f"Current: {current_people}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, status, (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.8, s_color, 3)

            data = {
                "ghat": GHAT_NAME,
                "entered": entered,
                "exited": exited,
                "current": current_people,
                "detected": len(new_people),
                "status": status,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }
            publish(data)

            display_frame = frame.copy()
            last_process_time = current_time
            show_frame(display_frame)

        if not HEADLESS and cv2.waitKey(20) & 0xFF == 27:
            return False

    return True


def main():
    if not init_firebase():
        raise SystemExit("Cannot start detector without Firebase credentials.")

    print("GodavariPro Detector Service started.")
    print(f"  Ghat:     {GHAT_NAME}")
    print(f"  Headless: {HEADLESS}")
    print(f"  Interval: {PROCESS_INTERVAL}s")

    while True:
        should_reconnect = run_stream()
        if not should_reconnect:
            break
        print("Reconnecting in 5 seconds...")
        time.sleep(5)

    if not HEADLESS:
        cv2.destroyAllWindows()
    print("Detector stopped.")


if __name__ == "__main__":
    main()
