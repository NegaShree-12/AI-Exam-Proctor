#!/usr/bin/env python3
"""
ProctorAI Client - ENHANCED EDITION with Superior Detection
- Better face detection with multiple algorithms
- Improved voice detection with continuous monitoring
- Object detection for phones, books, etc.
"""

import warnings
warnings.filterwarnings("ignore")

# Set memory limits FIRST
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
            print("[✅] PyTorch loaded")
        except ImportError:
            print("[⚠️] PyTorch not available")
    return torch

def lazy_import_speech():
    global sr
    if sr is None:
        try:
            import speech_recognition as sr
            print("[✅] Speech recognition loaded")
        except ImportError:
            print("[⚠️] Speech recognition not available")
    return sr

def lazy_import_yolo():
    global YOLO
    if YOLO is None:
        try:
            from ultralytics import YOLO
            print("[✅] YOLO loaded")
        except ImportError:
            print("[⚠️] YOLO not available")
    return YOLO

# =====================================
# 🔹 Configuration
# =====================================
SERVER_URL = "http://127.0.0.1:5000/log_data"

# Auto-exit configuration
SERIOUS_ALERTS = [
    "CELL PHONE detected!",
    "Multiple faces detected!",
    "BOOK detected!",
    "LAPTOP detected!"
]
CONSECUTIVE_SERIOUS_THRESHOLD = 5
EXIT_ON_SERIOUS_ALERT = True

parser = argparse.ArgumentParser(description="ProctorAI Client Agent")
parser.add_argument('--username', type=str, required=True, help="The student's username")
parser.add_argument('--exam_id', type=str, required=True, help="The unique ID for this exam")
parser.add_argument('--no-yolo', action='store_true', help="Disable YOLO to save memory")
parser.add_argument('--no-voice', action='store_true', help="Disable voice detection")
parser.add_argument('--low-res', action='store_true', help="Use lower resolution (320x240)")
parser.add_argument('--serious-threshold', type=int, default=5, help="Consecutive frames before exit")
args = parser.parse_args()

CONSECUTIVE_SERIOUS_THRESHOLD = args.serious_threshold

STUDENT_ID = args.username
EXAM_ID = args.exam_id
SESSION_ID = f"exam_{EXAM_ID}_{STUDENT_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

print(f"[🚀] Initializing ProctorAI Agent...")
print(f"    Student: {STUDENT_ID}")
print(f"    Exam ID: {EXAM_ID}")
print(f"    Session ID: {SESSION_ID}")

# Resolution settings
FRAME_WIDTH = 320 if args.low_res else 480
FRAME_HEIGHT = 240 if args.low_res else 360
print(f"[ℹ️] Using resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}")

# =====================================
# 🔹 Initialize YOLO
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
            print(f"[✅] YOLO model loaded on {device}")
        except Exception as e:
            print(f"[⚠️] Could not load YOLO model: {e}")
            yolo_model = None
else:
    print("[ℹ️] YOLO disabled")

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

# Face detection - IMPROVED
face_data = {
    "count": 0,
    "no_face": False,
    "multiple_faces": False,
    "confidence": 0
}
face_lock = threading.Lock()
no_face_start = None

# Serious violation tracking
serious_alert_counter = 0
serious_alert_message = ""
exam_terminated = False

SILENCE_TIMEOUT = 2  # Reduced to 2 seconds

# =====================================
# 🔹 IMPROVED VOICE DETECTION
# =====================================
def improved_voice_listener():
    """Continuous voice detection with better sensitivity"""
    if args.no_voice:
        return
        
    global voice_active, last_voice_time
    
    try:
        sr_module = lazy_import_speech()
        if not sr_module:
            return
            
        recognizer = sr_module.Recognizer()
        
        # Optimized settings for better detection
        recognizer.energy_threshold = 200  # Lower = more sensitive
        recognizer.dynamic_energy_threshold = True
        recognizer.dynamic_energy_adjustment_damping = 0.15
        recognizer.dynamic_energy_ratio = 1.5
        recognizer.pause_threshold = 0.8
        recognizer.operation_timeout = None
        recognizer.phrase_threshold = 0.3
        recognizer.non_speaking_duration = 0.5
        
        mic = sr_module.Microphone(sample_rate=16000)
        
        print("[🎤] Calibrating for ambient noise...")
        with mic as source:
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print(f"[🎤] Ambient noise level: {recognizer.energy_threshold}")
        
        print("[🎤] Voice detector ready - Continuous monitoring active")
        
        def listen_continuously():
            nonlocal recognizer, mic
            while running:
                try:
                    with mic as source:
                        print("[🎤] Listening...")
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        
                    try:
                        # Use Google for better accuracy
                        text = recognizer.recognize_google(audio, language="en-US", show_all=False)
                        if text and len(text.strip()) > 0:
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print(f"[🎤] [{timestamp}] Heard: {text}")
                            
                            with voice_lock:
                                voice_active = True
                                last_voice_time = time.time()
                                voice_text_queue.put({
                                    'text': text,
                                    'timestamp': timestamp
                                })
                                
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"[🎤] API error: {e}")
                    except Exception as e:
                        pass
                        
                except sr.WaitTimeoutError:
                    pass
                except Exception as e:
                    print(f"[🎤] Error: {e}")
                    time.sleep(0.1)
        
        # Start listening thread
        threading.Thread(target=listen_continuously, daemon=True).start()
        
    except Exception as e:
        print(f"[⚠️] Voice not available: {e}")

# =====================================
# 🔹 IMPROVED FACE DETECTION
# =====================================
class ImprovedFaceDetector:
    def __init__(self):
        self.face_cascades = []
        
        # Load multiple cascades for better detection
        cascade_paths = [
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml',
            cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml',
            cv2.data.haarcascades + 'haarcascade_profileface.xml'
        ]
        
        for path in cascade_paths:
            cascade = cv2.CascadeClassifier(path)
            if not cascade.empty():
                self.face_cascades.append(cascade)
        
        # DNN face detector (more accurate)
        self.use_dnn = False
        try:
            # Try to load DNN model if available
            model_file = "opencv_face_detector_uint8.pb"
            config_file = "opencv_face_detector.pbtxt"
            if os.path.exists(model_file) and os.path.exists(config_file):
                self.dnn_net = cv2.dnn.readNetFromTensorflow(model_file, config_file)
                self.use_dnn = True
                print("[Face] DNN face detector loaded")
        except:
            pass
        
        self.face_history = deque(maxlen=15)
        self.detection_history = deque(maxlen=30)
        
    def detect_faces_dnn(self, frame):
        """DNN-based face detection (more accurate)"""
        if not self.use_dnn:
            return []
            
        try:
            h, w = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123])
            self.dnn_net.setInput(blob)
            detections = self.dnn_net.forward()
            
            faces = []
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > 0.7:  # High confidence threshold
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    (x, y, x2, y2) = box.astype("int")
                    faces.append((x, y, x2-x, y2-y))
            return faces
        except:
            return []
    
    def detect_faces_cascade(self, gray):
        """Cascade-based face detection"""
        all_faces = []
        h, w = gray.shape
        
        for cascade in self.face_cascades:
            faces = cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50),
                maxSize=(int(w*0.8), int(h*0.8)),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            all_faces.extend(faces)
        
        return all_faces
    
    def merge_overlapping_faces(self, faces, threshold=0.3):
        """Merge overlapping face detections"""
        if len(faces) <= 1:
            return faces
            
        # Sort by area (largest first)
        faces = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)
        merged = []
        
        for face in faces:
            x, y, w, h = face
            overlapping = False
            
            for mface in merged:
                mx, my, mw, mh = mface
                
                # Calculate IoU
                xi1 = max(x, mx)
                yi1 = max(y, my)
                xi2 = min(x + w, mx + mw)
                yi2 = min(y + h, my + mh)
                
                if xi2 > xi1 and yi2 > yi1:
                    intersection = (xi2 - xi1) * (yi2 - yi1)
                    area1 = w * h
                    area2 = mw * mh
                    union = area1 + area2 - intersection
                    iou = intersection / union if union > 0 else 0
                    
                    if iou > threshold:
                        overlapping = True
                        break
            
            if not overlapping:
                merged.append(face)
        
        return merged
    
    def detect(self, frame):
        """Main detection method"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply preprocessing for better detection
            gray = cv2.equalizeHist(gray)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            all_faces = []
            
            # Try DNN first (more accurate)
            dnn_faces = self.detect_faces_dnn(frame)
            all_faces.extend(dnn_faces)
            
            # Also try cascade as backup
            cascade_faces = self.detect_faces_cascade(gray)
            all_faces.extend(cascade_faces)
            
            # Merge overlapping detections
            merged_faces = self.merge_overlapping_faces(all_faces)
            
            # Smooth with history
            self.detection_history.append(len(merged_faces))
            if len(self.detection_history) >= 5:
                # Use median of recent detections
                smoothed_count = int(np.median(list(self.detection_history)[-5:]))
            else:
                smoothed_count = len(merged_faces)
            
            return smoothed_count, merged_faces
            
        except Exception as e:
            print(f"[Face] Detection error: {e}")
            return 0, []

# =====================================
# 🔹 Thread Functions
# =====================================
def send_data_thread():
    """Send data to server"""
    while running:
        try:
            payload = data_to_send.get(timeout=1)
            time.sleep(0.1)
            
            try:
                response = requests.post(SERVER_URL, json=payload, timeout=2)
                if response.status_code != 200:
                    print(f"[HTTP] Error {response.status_code}")
            except Exception as e:
                print(f"[HTTP] Connection error: {e}")
                
        except queue.Empty:
            continue
        except Exception as e:
            print(f"[Network] Error: {e}")

def yolo_thread(frame_getter):
    """Object detection thread"""
    global yolo_results
    
    if not yolo_model:
        return
    
    frame_skip = 3  # Process every 3rd frame
    count = 0
    
    while running:
        frame = frame_getter()
        if frame is None:
            time.sleep(0.05)
            continue
        
        count += 1
        if count % frame_skip != 0:
            time.sleep(0.03)
            continue
            
        try:
            # Use smaller size for speed
            small_frame = cv2.resize(frame, (320, 240))
            results = yolo_model(small_frame, verbose=False, conf=0.4)
            
            if results and len(results) > 0:
                with yolo_lock:
                    yolo_results = results[0]
        except Exception as e:
            print(f"[YOLO] Error: {e}")
        
        time.sleep(0.05)

# =====================================
# 🔹 Main Program
# =====================================
if __name__ == "__main__":
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[❌] Error: Could not open camera.")
        sys.exit(1)

    # Optimize camera settings
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, 15)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)  # Disable autofocus for stability

    # Initialize detectors
    face_detector = ImprovedFaceDetector()
    
    # Frame getter
    current_frame = None
    def get_frame(): 
        return current_frame

    # Start threads
    print("[🚀] Starting all threads...")
    
    # Start voice listener
    if not args.no_voice:
        improved_voice_listener()
    
    # Start network thread
    threading.Thread(target=send_data_thread, daemon=True).start()
    
    # Start YOLO thread
    if yolo_model and not args.no_yolo:
        threading.Thread(target=yolo_thread, args=(get_frame,), daemon=True).start()
        print("[✅] YOLO detection active")
    else:
        print("[⚠️] YOLO detection disabled")

    print(f"[🎥] Camera started at {FRAME_WIDTH}x{FRAME_HEIGHT}")
    print("    Press 'q' to quit")

    try:
        frame_count = 0
        last_send_time = time.time()
        last_voice_check = time.time()
        
        # Statistics for debugging
        detection_stats = {
            'total_frames': 0,
            'faces_detected': 0,
            'voice_events': 0
        }
        
        while running and not exam_terminated:
            ret, frame = cap.read()
            if not ret:
                print("[⚠️] Frame read failed")
                time.sleep(0.1)
                continue
            
            current_frame = frame.copy()
            frame_count += 1
            detection_stats['total_frames'] += 1
            
            # Detect faces every frame for better accuracy
            face_count, face_boxes = face_detector.detect(frame)
            
            # Update face data
            with face_lock:
                face_data["count"] = face_count
                face_data["multiple_faces"] = (face_count > 1)
                
                # No face detection with timeout
                if face_count == 0:
                    if no_face_start is None:
                        no_face_start = time.time()
                    elif time.time() - no_face_start > 3:  # 3 seconds threshold
                        face_data["no_face"] = True
                    else:
                        face_data["no_face"] = False
                else:
                    face_data["no_face"] = False
                    no_face_start = None
                    detection_stats['faces_detected'] += 1
            
            # Check voice activity
            current_time = time.time()
            with voice_lock:
                if current_time - last_voice_time <= SILENCE_TIMEOUT:
                    voice_active = True
                else:
                    voice_active = False
            
            # Collect all alerts
            frame_alerts = set()
            has_serious_alert = False
            
            # Face alerts
            with face_lock:
                if face_data["multiple_faces"] and face_count > 1:
                    frame_alerts.add("Multiple faces detected!")
                    has_serious_alert = True
                if face_data["no_face"]:
                    frame_alerts.add("No person detected!")
            
            # Voice alerts
            voice_texts = []
            while not voice_text_queue.empty():
                voice_data = voice_text_queue.get()
                voice_texts.append(voice_data['text'])
                detection_stats['voice_events'] += 1
            
            if voice_active:
                frame_alerts.add("Someone is talking!")
                if voice_texts:
                    for text in voice_texts[-3:]:  # Last 3 voice detections
                        frame_alerts.add(f"VOICE: {text[:50]}")
            
            # YOLO object detection
            if yolo_model and not args.no_yolo:
                with yolo_lock:
                    if yolo_results and hasattr(yolo_results, 'boxes'):
                        try:
                            boxes = yolo_results.boxes.data.tolist()
                            for box in boxes:
                                if len(box) >= 6:
                                    conf, cls_id = box[4], box[5]
                                    if conf > 0.45:
                                        cls_name = yolo_results.names[int(cls_id)]
                                        if cls_name in ["cell phone", "laptop", "book"]:
                                            alert = f"{cls_name.upper()} detected!"
                                            frame_alerts.add(alert)
                                            has_serious_alert = True
                                            print(f"[📱] DETECTED: {cls_name} ({conf:.2f})")
                        except Exception as e:
                            pass
            
            # Check for serious violations
            if EXIT_ON_SERIOUS_ALERT and has_serious_alert:
                serious_alert_counter += 1
                serious_alert_message = next(
                    (a for a in frame_alerts if any(s in a for s in ["PHONE", "Multiple faces", "BOOK", "LAPTOP"])),
                    "Serious violation"
                )
                
                # Show warning
                cv2.putText(frame, f"⚠️ WARNING: {serious_alert_counter}/{CONSECUTIVE_SERIOUS_THRESHOLD}", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                if serious_alert_counter >= CONSECUTIVE_SERIOUS_THRESHOLD:
                    exam_terminated = True
                    print(f"\n{'='*60}")
                    print(f"❌ EXAM TERMINATED: {serious_alert_message}")
                    print(f"{'='*60}\n")
                    
                    # Send final alert
                    final_payload = {
                        "student_id": STUDENT_ID,
                        "session_id": SESSION_ID,
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "alerts": [f"EXAM_TERMINATED: {serious_alert_message}"],
                        "metrics": {"termination_reason": serious_alert_message}
                    }
                    try:
                        requests.post(SERVER_URL, json=final_payload, timeout=2)
                    except:
                        pass
                    
                    # Show termination screen
                    for i in range(5):
                        display = frame.copy()
                        cv2.putText(display, "❌ EXAM TERMINATED", (50, 100), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                        cv2.putText(display, f"Reason: {serious_alert_message}", (50, 150), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        cv2.imshow("ProctorAI Client", display)
                        cv2.waitKey(500)
                    
                    time.sleep(2)
                    break
            else:
                serious_alert_counter = max(0, serious_alert_counter - 1)
            
            # Draw face boxes for visualization
            for (x, y, w, h) in face_boxes:
                color = (0, 255, 0) if face_count == 1 else (0, 0, 255)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            
            # Display information
            y_offset = 30
            cv2.putText(frame, f"Faces: {face_count}", (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            y_offset += 20
            cv2.putText(frame, f"Voice: {'ACTIVE' if voice_active else 'inactive'}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                       (0, 255, 0) if voice_active else (100, 100, 100), 1)
            
            # Show alerts
            y_offset += 25
            for alert in list(frame_alerts)[:4]:
                cv2.putText(frame, f"• {alert}", (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                y_offset += 18
            
            cv2.imshow("ProctorAI Client", frame)
            
            # Send data periodically
            if time.time() - last_send_time >= 2.0 and not exam_terminated:
                payload = {
                    "student_id": STUDENT_ID,
                    "session_id": SESSION_ID,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "alerts": list(frame_alerts)[:10],
                    "metrics": {
                        "face_count": face_count,
                        "multiple_faces": face_count > 1,
                        "no_face": face_data["no_face"],
                        "voice_active": voice_active,
                        "voice_texts": voice_texts[-3:] if voice_texts else [],
                        "detected_objects": [a for a in frame_alerts if any(x in a for x in ["PHONE", "BOOK", "LAPTOP"])]
                    }
                }
                try:
                    data_to_send.put_nowait(payload)
                    last_send_time = time.time()
                    
                    if frame_alerts:
                        print(f"[📤] Alerts: {list(frame_alerts)}")
                    if voice_texts:
                        print(f"[📤] Voice: {voice_texts}")
                        
                except queue.Full:
                    pass
            
            # Handle quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Periodic stats
            if frame_count % 100 == 0:
                print(f"\n[Stats] Frames: {detection_stats['total_frames']}, "
                      f"Faces detected: {detection_stats['faces_detected']}, "
                      f"Voice events: {detection_stats['voice_events']}\n")
                gc.collect()

    except KeyboardInterrupt:
        print("\n[🛑] Interrupted")
    finally:
        running = False
        print("[⚙️] Shutting down...")
        cap.release()
        cv2.destroyAllWindows()
        time.sleep(0.5)
        
        if exam_terminated:
            print(f"\n❌ Exam terminated: {serious_alert_message}")
        else:
            print("\n✅ Exam completed")