import cv2
from ultralytics import YOLO
import torch

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    device = 0
else:
    print("No GPU available, using CPU")
    device = 'cpu'

model = YOLO("yolov8n.pt")  

cap = cv2.VideoCapture(0)   

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame, device=device)  
    annotated = results[0].plot()

    cv2.imshow("Baseball Tracker - Test", annotated)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()