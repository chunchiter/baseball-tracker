import cv2
from ultralytics import YOLO
import torch
from collections import deque
import numpy as np
import json
import time
import matplotlib.pyplot as plt
from datetime import datetime

MODEL_PATH = "runs/detect/runs/baseball_detector/weights/best.pt"
TRAIL_LENGTH = 30
CONF_THRESHOLD = 0.3

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(0)
trail = deque(maxlen=TRAIL_LENGTH)

# Trayectoria del lanzamiento actual
current_throw = []
all_throws = []
last_save_time = time.time()
throwing = False
no_detect_count = 0

print(f"GPU: {torch.cuda.get_device_name(0)}")
print("Presiona Q para salir | G para ver gráfica | S para guardar")

def save_trajectory(throws):
    filename = f"trajectories/throw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import os
    os.makedirs("trajectories", exist_ok=True)
    with open(filename, "w") as f:
        json.dump(throws, f)
    print(f"Guardado: {filename}")
    return filename

def show_graph(throw_points):
    if len(throw_points) < 2:
        print("No hay suficientes puntos para graficar")
        return

    xs = [p[0] for p in throw_points]
    ys = [p[1] for p in throw_points]

    # Invertir Y porque en imagen Y crece hacia abajo
    ys = [max(ys) - y + min(ys) for y in ys]

    plt.figure(figsize=(10, 5))
    plt.plot(xs, ys, 'r-o', markersize=4, linewidth=2)
    plt.scatter(xs[0], ys[0], color='green', s=100, zorder=5, label='Inicio')
    plt.scatter(xs[-1], ys[-1], color='blue', s=100, zorder=5, label='Final')
    plt.title("Trayectoria del lanzamiento")
    plt.xlabel("Posición X (píxeles)")
    plt.ylabel("Posición Y (píxeles)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

while True:
    ret, frame = cap.read()
    if not ret:
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

    # Lógica de detección de lanzamiento
    if ball_center:
        no_detect_count = 0
        throwing = True
        current_throw.append(list(ball_center))
        trail.append(ball_center)
    else:
        no_detect_count += 1
        trail.append(None)

        # Si dejó de detectar por 20 frames = lanzamiento terminó
        if throwing and no_detect_count > 20:
            if len(current_throw) > 5:
                all_throws.append(current_throw.copy())
                save_trajectory(current_throw)
                print(f"Lanzamiento guardado con {len(current_throw)} puntos")
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
    cv2.putText(frame, f"Estado: {status}", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    cv2.putText(frame, f"Lanzamientos: {len(all_throws)}", (10, 60),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, f"Puntos actuales: {len(current_throw)}", (10, 90),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Baseball Tracker", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break
    elif key == ord("g"):
        # Mostrar gráfica del último lanzamiento
        if all_throws:
            show_graph(all_throws[-1])
        elif current_throw:
            show_graph(current_throw)
        else:
            print("No hay lanzamientos grabados aún")
    elif key == ord("s"):
        if current_throw:
            save_trajectory(current_throw)

cap.release()
cv2.destroyAllWindows()