import cv2
from ultralytics import YOLO
import torch
from collections import deque
import numpy as np
import json
import time
import os
import matplotlib.pyplot as plt
from datetime import datetime

MODEL_PATH = "runs/detect/runs/baseball_detector/weights/best.pt"
TRAIL_LENGTH = 30
CONF_THRESHOLD = 0.3
SESSION_TIMEOUT = 3600

# Calibración de velocidad
FPS = 30                    # fps de tu webcam
PIXELS_PER_METER = 200      # ajustar según distancia de la cámara
                            # 200px ≈ 1 metro a ~2m de distancia

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(0)   # 0 para webcam, 1  primera cámara externa USB, etc.
                            # Si la cámara es IP (por red WiFi) // cap = cv2.VideoCapture("rtsp://192.168.1.100:554/stream")
#Si la cámara soporta mayor FPS
#cap = cv2.VideoCapture(1)  # nueva cámara
#cap.set(cv2.CAP_PROP_FPS, 120)        # pedir 120 fps
#cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)   # resolución
#cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


# Intentar obtener FPS real de la cámara
real_fps = cap.get(cv2.CAP_PROP_FPS)
if real_fps > 0:
    FPS = real_fps
print(f"FPS de camara: {FPS}")

trail = deque(maxlen=TRAIL_LENGTH)
positions_with_time = deque(maxlen=10)  # guarda (x, y, timestamp)

os.makedirs("trajectories", exist_ok=True)
session_name = f"trajectories/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
session_data = {"date": datetime.now().isoformat(), "throws": []}
session_start = time.time()

current_throw = []
throwing = False
no_detect_count = 0
current_speed_kmh = 0
max_speed_kmh = 0
throw_max_speeds = []

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Sesion: {session_name}")
print("Q=salir | G=grafica | C=calibrar")

def save_session():
    with open(session_name, "w") as f:
        json.dump(session_data, f, indent=2)

def calculate_speed(positions):
    if len(positions) < 2:
        return 0
    # Toma los últimos 2 puntos con tiempo
    (x1, y1, t1) = positions[-2]
    (x2, y2, t2) = positions[-1]

    dt = t2 - t1
    if dt <= 0:
        return 0

    # Distancia en píxeles
    dist_px = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)

    # Convertir a metros
    dist_m = dist_px / PIXELS_PER_METER

    # Velocidad en m/s y luego km/h
    speed_ms = dist_m / dt
    speed_kmh = speed_ms * 3.6

    return round(speed_kmh, 1)

def show_graph(throw_data):
    points = throw_data["points"]
    speeds = throw_data.get("speeds", [])
    max_spd = throw_data.get("max_speed_kmh", 0)

    if len(points) < 2:
        print("No hay suficientes puntos")
        return

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ys_inv = [max(ys) - y + min(ys) for y in ys]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Gráfica de trayectoria
    ax1.plot(xs, ys_inv, 'r-o', markersize=4, linewidth=2)
    ax1.scatter(xs[0], ys_inv[0], color='green', s=150, zorder=5, label='Inicio')
    ax1.scatter(xs[-1], ys_inv[-1], color='blue', s=150, zorder=5, label='Final')
    ax1.set_title(f"Trayectoria — Max: {max_spd} km/h")
    ax1.set_xlabel("Posicion X (pixeles)")
    ax1.set_ylabel("Posicion Y (pixeles)")
    ax1.legend()
    ax1.grid(True)

    # Gráfica de velocidad
    if speeds:
        ax2.plot(speeds, 'b-', linewidth=2)
        ax2.axhline(y=max_spd, color='r', linestyle='--', label=f'Max: {max_spd} km/h')
        ax2.fill_between(range(len(speeds)), speeds, alpha=0.3, color='blue')
        ax2.set_title("Velocidad durante el lanzamiento")
        ax2.set_xlabel("Frame")
        ax2.set_ylabel("Velocidad (km/h)")
        ax2.legend()
        ax2.grid(True)

    plt.tight_layout()
    plt.show()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    if time.time() - session_start > SESSION_TIMEOUT:
        print("Sesion cerrada por tiempo")
        break

    now = time.time()
    results = model(frame, device=0, conf=CONF_THRESHOLD, verbose=False)
    ball_center = None

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2
            ball_center = (cx, cy)

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"baseball {conf:.2f}"
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

    if ball_center:
        no_detect_count = 0
        throwing = True
        positions_with_time.append((ball_center[0], ball_center[1], now))
        current_throw.append(list(ball_center))
        trail.append(ball_center)

        # Calcular velocidad
        if len(positions_with_time) >= 2:
            current_speed_kmh = calculate_speed(positions_with_time)
            if current_speed_kmh > max_speed_kmh:
                max_speed_kmh = current_speed_kmh

    else:
        no_detect_count += 1
        trail.append(None)

        if throwing and no_detect_count > 20:
            if len(current_throw) > 5:
                # Recalcular velocidades del lanzamiento completo
                speeds = []
                for i in range(1, len(current_throw)):
                    p1 = current_throw[i-1]
                    p2 = current_throw[i]
                    dist_px = np.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
                    dist_m = dist_px / PIXELS_PER_METER
                    spd = round((dist_m * FPS) * 3.6, 1)
                    speeds.append(spd)

                throw_data = {
                    "points": current_throw.copy(),
                    "speeds": speeds,
                    "max_speed_kmh": max_speed_kmh,
                    "avg_speed_kmh": round(np.mean(speeds), 1) if speeds else 0
                }
                session_data["throws"].append(throw_data)
                throw_max_speeds.append(max_speed_kmh)
                save_session()
                print(f"Lanzamiento {len(session_data['throws'])} — Max: {max_speed_kmh} km/h")

            current_throw = []
            max_speed_kmh = 0
            current_speed_kmh = 0
            positions_with_time.clear()
            throwing = False

    # Dibujar trayectoria con color según velocidad
    for i in range(1, len(trail)):
        if trail[i] is None or trail[i - 1] is None:
            continue
        thickness = int(np.sqrt(TRAIL_LENGTH / float(i + 1)) * 2.5)
        cv2.line(frame, trail[i - 1], trail[i], (0, 0, 255), thickness)

    # Info en pantalla
    status = "DETECTANDO" if throwing else "ESPERANDO"
    color = (0, 255, 0) if throwing else (0, 0, 255)
    elapsed = int(time.time() - session_start)
    mins = elapsed // 60
    secs = elapsed % 60

    cv2.putText(frame, f"Estado: {status}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(frame, f"Velocidad: {current_speed_kmh} km/h", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"Max sesion: {max(throw_max_speeds) if throw_max_speeds else 0} km/h", (10, 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 165, 0), 2)
    cv2.putText(frame, f"Lanzamientos: {len(session_data['throws'])}", (10, 120),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Sesion: {mins:02d}:{secs:02d}", (10, 150),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow("Baseball Tracker", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        save_session()
        print(f"Sesion guardada — {len(session_data['throws'])} lanzamientos")
        if throw_max_speeds:
            print(f"Velocidad maxima de la sesion: {max(throw_max_speeds)} km/h")
        break
    elif key == ord("g"):
        if session_data["throws"]:
            show_graph(session_data["throws"][-1])
        else:
            print("No hay lanzamientos aun")

cap.release()
cv2.destroyAllWindows()