import cv2
from ultralytics import YOLO
import torch
from collections import deque
import numpy as np
import time
import json
import os
from datetime import datetime

MODEL_PATH = "runs/detect/runs/baseball_detector/weights/best.pt"
TRAIL_LENGTH = 30
CONF_THRESHOLD = 0.3
PIXELS_PER_METER = 200

class BaseballTracker:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)
        self.cap = cv2.VideoCapture(0)
        self.trail = deque(maxlen=TRAIL_LENGTH)
        self.positions_with_time = deque(maxlen=10)
        self.current_throw = []
        self.throwing = False
        self.no_detect_count = 0
        self.current_speed_kmh = 0
        self.max_speed_kmh = 0
        self.throw_max_speeds = []
        self.running = False

        # Sesión
        os.makedirs("trajectories", exist_ok=True)
        self.session_name = f"trajectories/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.session_data = {"date": datetime.now().isoformat(), "throws": []}

        # Estado actual para la API
        self.current_state = {
            "detecting": False,
            "speed_kmh": 0,
            "max_speed_kmh": 0,
            "total_throws": 0,
            "trail": [],
            "last_throw": None
        }

        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30

    def calculate_speed(self, positions):
        if len(positions) < 2:
            return 0
        (x1, y1, t1) = positions[-2]
        (x2, y2, t2) = positions[-1]
        dt = t2 - t1
        if dt <= 0:
            return 0
        dist_px = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        dist_m = dist_px / PIXELS_PER_METER
        return round((dist_m / dt) * 3.6, 1)

    def save_session(self):
        with open(self.session_name, "w") as f:
            json.dump(self.session_data, f, indent=2)

    def process_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        now = time.time()
        results = self.model(frame, device=0, conf=CONF_THRESHOLD, verbose=False)
        ball_center = None

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cx = (x1 + x2) // 2
                cy = (y1 + y2) // 2
                ball_center = (cx, cy)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"baseball {conf:.2f}", (x1, y1 - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

        if ball_center:
            self.no_detect_count = 0
            self.throwing = True
            self.positions_with_time.append((ball_center[0], ball_center[1], now))
            self.current_throw.append(list(ball_center))
            self.trail.append(ball_center)
            self.current_speed_kmh = self.calculate_speed(self.positions_with_time)
            if self.current_speed_kmh > self.max_speed_kmh:
                self.max_speed_kmh = self.current_speed_kmh
        else:
            self.no_detect_count += 1
            self.trail.append(None)

            if self.throwing and self.no_detect_count > 20:
                if len(self.current_throw) > 5:
                    speeds = []
                    for i in range(1, len(self.current_throw)):
                        p1 = self.current_throw[i-1]
                        p2 = self.current_throw[i]
                        dist_px = np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                        spd = round((dist_px / PIXELS_PER_METER * self.fps) * 3.6, 1)
                        speeds.append(spd)

                    throw_data = {
                        "points": self.current_throw.copy(),
                        "speeds": speeds,
                        "max_speed_kmh": self.max_speed_kmh,
                        "avg_speed_kmh": round(np.mean(speeds), 1) if speeds else 0,
                        "timestamp": datetime.now().isoformat()
                    }
                    self.session_data["throws"].append(throw_data)
                    self.throw_max_speeds.append(self.max_speed_kmh)
                    self.save_session()
                    self.current_state["last_throw"] = throw_data

                self.current_throw = []
                self.max_speed_kmh = 0
                self.current_speed_kmh = 0
                self.positions_with_time.clear()
                self.throwing = False

        # Dibujar trayectoria
        for i in range(1, len(self.trail)):
            if self.trail[i] is None or self.trail[i-1] is None:
                continue
            thickness = int(np.sqrt(TRAIL_LENGTH / float(i + 1)) * 2.5)
            cv2.line(frame, self.trail[i-1], self.trail[i], (0, 0, 255), thickness)

        # Actualizar estado para API
        self.current_state.update({
            "detecting": self.throwing,
            "speed_kmh": self.current_speed_kmh,
            "max_speed_kmh": max(self.throw_max_speeds) if self.throw_max_speeds else 0,
            "total_throws": len(self.session_data["throws"]),
            "trail": [list(p) if p else None for p in self.trail]
        })

        return frame, self.current_state

    def release(self):
        self.save_session()
        self.cap.release()