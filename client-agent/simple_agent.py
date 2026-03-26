#!/usr/bin/env python3
"""
Simple ProctorAI Client - Guaranteed to work
- Sends test alerts regularly
- No dependencies on YOLO or heavy libraries
"""

import requests
import time
import random
import sys
import argparse
from datetime import datetime

SERVER_URL = "http://127.0.0.1:5000/log_data"

parser = argparse.ArgumentParser(description="Simple ProctorAI Client")
parser.add_argument('--username', type=str, required=True)
parser.add_argument('--exam_id', type=str, required=True)
parser.add_argument('--session_id', type=str, required=True)
parser.add_argument('--background', action='store_true')
args = parser.parse_args()

STUDENT_ID = args.username
EXAM_ID = args.exam_id
SESSION_ID = args.session_id

print(f"🚀 Simple ProctorAI Client Starting...")
print(f"   Student: {STUDENT_ID}")
print(f"   Session: {SESSION_ID}")
print(f"   Server: {SERVER_URL}")

# List of possible alerts
ALERTS = [
    "CELL PHONE detected!",
    "Multiple faces detected!",
    "Someone is talking!",
    "No person detected!",
    "BOOK detected!",
    "LAPTOP detected!",
    "VOICE: I need help with this question",
    "WEB: Switched tabs",
    "WEB: Left focus"
]

def calculate_score(alerts):
    """Calculate integrity score based on alerts"""
    score = 100
    
    for alert in alerts:
        if "CELL PHONE" in alert:
            score -= 40
        elif "Multiple faces" in alert:
            score -= 35
        elif "LAPTOP" in alert:
            score -= 30
        elif "BOOK" in alert:
            score -= 25
        elif "No person" in alert:
            score -= 20
        elif "Someone is talking" in alert:
            score -= 10
        elif "VOICE:" in alert:
            score -= 8
        elif "Switched tabs" in alert:
            score -= 5
        elif "Left focus" in alert:
            score -= 3
    
    return max(0, score)

def send_data():
    """Send simulated proctoring data"""
    try:
        # Randomly select 0-3 alerts
        num_alerts = random.randint(0, 3)
        alerts = random.sample(ALERTS, num_alerts) if num_alerts > 0 else []
        
        # Calculate score
        score = calculate_score(alerts)
        
        # Create payload
        payload = {
            "source": "python_agent",
            "student_id": STUDENT_ID,
            "session_id": SESSION_ID,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "alerts": alerts,
            "metrics": {
                "face_count": random.randint(0, 2),
                "voice_active": len([a for a in alerts if "VOICE:" in a]) > 0,
                "detected_objects": [a for a in alerts if any(x in a for x in ["PHONE", "BOOK", "LAPTOP"])]
            }
        }
        
        # Send to server
        response = requests.post(SERVER_URL, json=payload, timeout=5)
        
        if response.status_code == 200:
            timestamp = datetime.now().strftime("%H:%M:%S")
            if alerts:
                print(f"[{timestamp}] ✅ Sent: {', '.join(alerts)} (Score: {score})")
            else:
                print(f"[{timestamp}] ✅ Heartbeat sent (Score: {score})")
            return True
        else:
            print(f"[{timestamp}] ❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

# Main loop
print("\n" + "="*50)
print("🎯 Agent running - sending data every 3 seconds")
print("   Press Ctrl+C to stop")
print("="*50 + "\n")

try:
    counter = 0
    while True:
        counter += 1
        success = send_data()
        
        if counter % 10 == 0:
            print(f"\n📊 Stats: {counter} updates sent\n")
        
        time.sleep(3)
        
except KeyboardInterrupt:
    print("\n\n🛑 Stopping agent...")
    print("✅ Done")

print(f"\n📋 Check debug: {SERVER_URL.replace('/log_data', '/api/debug/session/' + SESSION_ID)}")