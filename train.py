from ultralytics import YOLO

if __name__ == '__main__':
    model = YOLO("yolov8n.pt")

    results = model.train(
        data="dataset/data.yaml",
        epochs=50,
        imgsz=640,
        batch=16,
        device=0,
        workers=0,
        project="runs",
        name="baseball_detector",
        exist_ok=True,
        patience=10,
        save=True,
        plots=True
    )

    print("Entrenamiento completado!")
    print("Mejor modelo: runs/baseball_detector/weights/best.pt")