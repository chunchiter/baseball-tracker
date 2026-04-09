import cv2
from ultralytics import YOLO
import torch

print(f"GPU: {torch.cuda.get_device_name(0)}")

# Usa tu modelo entrenado
model = YOLO("runs/detect/runs/baseball_detector/weights/best.pt")

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, device=0, conf=0.5)
    annotated = results[0].plot()

    cv2.imshow("Baseball Tracker", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()