from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import threading
import cv2
import base64
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.tracker import BaseballTracker

app = FastAPI(title="Baseball Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

tracker = BaseballTracker()
latest_frame = None
latest_state = {}
tracker_lock = threading.Lock()

def run_tracker():
    global latest_frame, latest_state
    while True:
        frame, state = tracker.process_frame()
        if frame is None:
            break
        with tracker_lock:
            latest_frame = frame.copy()
            latest_state = state.copy() if state else {}

tracker_thread = threading.Thread(target=run_tracker, daemon=True)
tracker_thread.start()

@app.get("/")
def root():
    return {"status": "Baseball Tracker API corriendo"}

@app.get("/session")
def get_session():
    return tracker.session_data

@app.get("/state")
def get_state():
    with tracker_lock:
        return latest_state

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Cliente conectado via WebSocket")
    try:
        while True:
            with tracker_lock:
                state = latest_state.copy()
                frame = latest_frame.copy() if latest_frame is not None else None

            if frame is not None:
                # Codificar frame como base64 para enviarlo
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                frame_b64 = base64.b64encode(buffer).decode('utf-8')
                state["frame"] = frame_b64

            await websocket.send_text(json.dumps(state))
            await asyncio.sleep(0.033)  # ~30fps
    except WebSocketDisconnect:
        print("Cliente desconectado")