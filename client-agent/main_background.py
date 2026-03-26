#!/usr/bin/env python3
"""
ProctorAI Client - BACKGROUND MODE (No Window)
- Runs completely in background
- No GUI, no popups
- Automatically starts/stops with exam
"""

import warnings
warnings.filterwarnings("ignore")

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import sys
import time
import threading
from collections import deque
from datetime import datetime
import queue
import requests
import argparse
import gc
import json
import cv2
import numpy as np

# Lazy imports
torch = None
sr = None
YOLO = None

def lazy_import_torch():
    global torch
    if torch is None:
        try:
            import torch
            print("[✓] PyTorch loaded")
        except ImportError:
            print("[✗] PyTorch not available")
    return torch

def lazy_import_speech():
    global sr
    if sr is None:
        try:
            import speech_recognition as sr
            print("[✓] Speech recognition loaded")
        except ImportError:
            print("[✗] Speech recognition not available")
    return sr

def lazy_import_yolo():
    global YOLO
    if YOLO is None:
        try:
            from ultralytics import YOLO
            print("[✓] YOLO loaded")
        except ImportError:
            print("[✗] YOLO not available")
    return YOLO

# =====================================
# 🔹 Configuration
# =====================================
SERVER_URL = "http://127.0.0.1:5000/log_data"

parser = argparse.ArgumentParser(description="ProctorAI Client - Background Mode")
parser.add_argument('--username', type=str, required=True, help="Student username")
parser.add_argument('--exam_id', type=str, required=True, help="Exam ID")
parser.add_argument('--session_id', type=str, required=True, help="Session ID")
parser.add_argument('--no-yolo', action='store_true', help="Disable YOLO")
parser.add_argument('--no-voice', action='store_true', help="Disable voice")
args = parser.parse_args()

STUDENT_ID = args.username
EXAM_ID = args.exam_id
SESSION_ID = args.session_id

print(f"[🚀] Starting ProctorAI Background Agent...")
print(f"    Student: {STUDENT_ID}")
print(f"    Session: {SESSION_ID}")

# Resolution (lower for better performance)
FRAME_WIDTH = 320
FRAME_HEIGHT = 240

# =====================================
# 🔹 Initialize YOLO (optional)
# =====================================
yolo_model = None
yolo_results = None
yolo_lock = threading.Lock()

if not args.no_yolo:
    YOLO_class = lazy_import_yolo()
    if YOLO_class:
        try:
            print("[⏳] Loading YOLO model...")
            yolo_model = YOLO_class("yolov8n.pt")
            torch = lazy_import_torch()
            if torch:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                yolo_model.to(device)
            print(f"[✓] YOLO model loaded on {device}")
        except Exception as e:
            print(f"[✗] Could not load YOLO: {e}")
            yolo_model = None

# =====================================
# 🔹 Global Variables
# =====================================
running = True
data_to_send = queue.Queue(maxsize=20)

# Voice detection
voice_active = False
last_voice_time = 0
voice_text_queue = queue.Queue()
voice_lock = threading.Lock()

# Face detection
face_data = {
    "count": 0,
    "no_face": False,
    "multiple_faces": False
}
face_lock = threading.Lock()
no_face_start = None

SILENCE_TIMEOUT = 2

# =====================================
# 🔹 Face Detector (Optimized)
# =====================================
class BackgroundFaceDetector:
    def __init__(self):
        # Load cascade once
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.detection_history = deque(maxlen=10)
        
    def detect(self, frame):
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50)
            )
            
            face_count = len(faces)
            self.detection_history.append(face_count)
            
            # Smooth detection
            if len(self.detection_history) >= 3:
                smoothed = int(np.median(list(self.detection_history)[-3:]))
            else:
                smoothed = face_count
                
            return smoothed, faces
            
        except Exception as e:
            print(f"[Face] Error: {e}")
            return 0, []

# =====================================
# 🔹 Voice Detection
# =====================================
def background_voice_listener():
    """Voice detection running in background"""
    if args.no_voice:
        return
        
    global voice_active, last_voice_time
    
    try:
        sr_module = lazy_import_speech()
        if not sr_module:
            return
            
        recognizer = sr_module.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.8
        
        mic = sr_module.Microphone()
        
        print("[🎤] Calibrating microphone...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("[🎤] Voice monitoring active (background)")
        
        def listen():
            while running:
                try:
                    with mic as source:
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                        
                    try:
                        text = recognizer.recognize_google(audio)
                        if text:
                            with voice_lock:
                                voice_active = True
                                last_voice_time = time.time()
                                voice_text_queue.put(text)
                                print(f"[🎤] Heard: {text[:50]}")
                    except:
                        pass
                except:
                    time.sleep(0.1)
        
        threading.Thread(target=listen, daemon=True).start()
        
    except Exception as e:
        print(f"[✗] Voice not available: {e}")

# =====================================
# 🔹 Data Sender
# =====================================
def send_data():
    """Send data to server"""
    while running:
        try:
            payload = data_to_send.get(timeout=1)
            
            try:
                response = requests.post(SERVER_URL, json=payload, timeout=2)
                if response.status_code != 200:
                    print(f"[HTTP] Error {response.status_code}")
            except Exception as e:
                print(f"[HTTP] Connection error: {e}")
                
        except queue.Empty:
            continue

# =====================================
# 🔹 YOLO Thread
# =====================================
def yolo_detection(frame_getter):
    """Object detection in separate thread"""
    global yolo_results
    
    if not yolo_model:
        return
    
    frame_count = 0
    while running:
        frame = frame_getter()
        if frame is None:
            time.sleep(0.1)
            continue
        
        frame_count += 1
        if frame_count % 5 != 0:  # Process every 5th frame
            time.sleep(0.05)
            continue
            
        try:
            small = cv2.resize(frame, (320, 240))
            results = yolo_model(small, verbose=False, conf=0.5)
            
            if results and len(results) > 0:
                with yolo_lock:
                    yolo_results = results[0]
        except Exception as e:
            pass
        
        time.sleep(0.1)

# =====================================
# 🔹 Main - BACKGROUND MODE (NO WINDOW)
# =====================================
if __name__ == "__main__":
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[❌] Could not open camera")
        sys.exit(1)

    # Optimize camera
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 10)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Initialize detector
    face_detector = BackgroundFaceDetector()
    
    # Frame getter
    current_frame = None
    def get_frame(): 
        return current_frame

    # Start threads
    print("[🚀] Starting background threads...")
    
    if not args.no_voice:
        background_voice_listener()
    
    threading.Thread(target=send_data, daemon=True).start()
    
    if yolo_model and not args.no_yolo:
        threading.Thread(target=yolo_detection, args=(get_frame,), daemon=True).start()
    
    print("[✓] Proctoring active (running in background)")
    print("[i] Press Ctrl+C to stop")
    
    try:
        last_send = time.time()
        
        while running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            
            current_frame = frame.copy()
            
            # Detect faces
            face_count, face_boxes = face_detector.detect(frame)
            
            # Update face data
            with face_lock:
                face_data["count"] = face_count
                face_data["multiple_faces"] = (face_count > 1)
                
                if face_count == 0:
                    if no_face_start is None:
                        no_face_start = time.time()
                    elif time.time() - no_face_start > 3:
                        face_data["no_face"] = True
                else:
                    face_data["no_face"] = False
                    no_face_start = None
            
            # Check voice
            with voice_lock:
                if time.time() - last_voice_time <= SILENCE_TIMEOUT:
                    voice_active = True
                else:
                    voice_active = False
            
            # Collect alerts
            alerts = []
            
            if face_data["multiple_faces"]:
                alerts.append("Multiple faces detected!")
            if face_data["no_face"]:
                alerts.append("No person detected!")
            if voice_active:
                alerts.append("Someone is talking!")
            
            # Voice texts
            voice_texts = []
            while not voice_text_queue.empty():
                voice_texts.append(voice_text_queue.get())
                if voice_texts:
                    alerts.append(f"VOICE: {voice_texts[-1][:30]}")
            
            # YOLO detection
            if yolo_model and not args.no_yolo:
                with yolo_lock:
                    if yolo_results and hasattr(yolo_results, 'boxes'):
                        try:
                            boxes = yolo_results.boxes.data.tolist()
                            for box in boxes:
                                if len(box) >= 6:
                                    conf, cls_id = box[4], box[5]
                                    if conf > 0.5:
                                        name = yolo_results.names[int(cls_id)]
                                        if name in ["cell phone", "laptop", "book"]:
                                            alerts.append(f"{name.upper()} detected!")
                        except:
                            pass
            
            # Send data periodically
            if time.time() - last_send >= 3.0:  # Send every 3 seconds
                payload = {
                    "student_id": STUDENT_ID,
                    "session_id": SESSION_ID,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "alerts": alerts[:10],
                    "metrics": {
                        "face_count": face_count,
                        "voice_active": voice_active
                    }
                }
                try:
                    data_to_send.put_nowait(payload)
                    last_send = time.time()
                    
                    if alerts:
                        print(f"[📤] Alerts: {alerts}")
                        
                except queue.Full:
                    pass
            
            # Small delay to prevent CPU overload
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        print("\n[🛑] Stopping...")
    finally:
        running = False
        cap.release()
        print("[✓] Camera closed")
        print("[✓] Proctoring stopped")
