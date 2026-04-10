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
SESSION_TIMEOUT = 3600  # 1 hora en segundos

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(0)
trail = deque(maxlen=TRAIL_LENGTH)

# Sistema de sesiones
os.makedirs("trajectories", exist_ok=True)
session_name = f"trajectories/session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
session_data = {"date": datetime.now().isoformat(), "throws": []}
session_start = time.time()

current_throw = []
throwing = False
no_detect_count = 0

print(f"GPU: {torch.cuda.get_device_name(0)}")
print(f"Sesion iniciada: {session_name}")
print("Presiona Q para salir | G para ver grafica")

def save_session():
    with open(session_name, "w") as f:
        json.dump(session_data, f, indent=2)

def show_graph(throw_points):
    if len(throw_points) < 2:
        print("No hay suficientes puntos")
        return
    xs = [p[0] for p in throw_points]
    ys = [p[1] for p in throw_points]
    ys = [max(ys) - y + min(ys) for y in ys]
    plt.figure(figsize=(10, 5))
    plt.plot(xs, ys, 'r-o', markersize=4, linewidth=2)
    plt.scatter(xs[0], ys[0], color='green', s=150, zorder=5, label='Inicio')
    plt.scatter(xs[-1], ys[-1], color='blue', s=150, zorder=5, label='Final')
    plt.title(f"Lanzamiento #{len(session_data['throws'])}")
    plt.xlabel("Posicion X (pixeles)")
    plt.ylabel("Posicion Y (pixeles)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Verificar timeout de sesion
    if time.time() - session_start > SESSION_TIMEOUT:
        print("Sesion cerrada por tiempo (1 hora)")
        break

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
        current_throw.append(list(ball_center))
        trail.append(ball_center)
    else:
        no_detect_count += 1
        trail.append(None)

        if throwing and no_detect_count > 20:
            if len(current_throw) > 5:
                session_data["throws"].append(current_throw.copy())
                save_session()
                print(f"Lanzamiento {len(session_data['throws'])} guardado")
            current_throw = []
            throwing = False

    # Dibujar trayectoria
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
    cv2.putText(frame, f"Lanzamientos: {len(session_data['throws'])}", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Sesion: {mins:02d}:{secs:02d}", (10, 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    cv2.imshow("Baseball Tracker", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        save_session()
        print(f"Sesion guardada con {len(session_data['throws'])} lanzamientos")
        break
    elif key == ord("g"):
        if session_data["throws"]:
            show_graph(session_data["throws"][-1])
        else:
            print("No hay lanzamientos aun")

cap.release()
cv2.destroyAllWindows()