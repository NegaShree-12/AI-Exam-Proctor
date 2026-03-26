# backend/test_client.py
import requests
import time
import random
from datetime import datetime

API_URL = "http://127.0.0.1:5000"

def send_test_data(session_id, student_id):
    """Send simulated proctoring data"""
    
    alerts_options = [
        "Multiple faces detected!",
        "CELL PHONE detected!",
        "Someone is talking!",
        "No person detected!",
        "BOOK detected!",
        "LAPTOP detected!"
    ]
    
    print(f"📤 Sending test data for session: {session_id}")
    
    for i in range(10):  # Send 10 batches of data
        # Randomly select 0-2 alerts
        num_alerts = random.randint(0, 2)
        alerts = random.sample(alerts_options, num_alerts) if num_alerts > 0 else []
        
        # Calculate score based on alerts
        score = 100
        if "CELL PHONE detected!" in alerts:
            score -= 40
        if "Multiple faces detected!" in alerts:
            score -= 35
        if "LAPTOP detected!" in alerts:
            score -= 30
        if "BOOK detected!" in alerts:
            score -= 25
        if "No person detected!" in alerts:
            score -= 20
        if "Someone is talking!" in alerts:
            score -= 10
        
        payload = {
            "source": "test_client",
            "student_id": student_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "alerts": alerts,
            "metrics": {
                "face_count": random.randint(0, 2),
                "voice_active": random.choice([True, False]),
                "test_data": True,
                "iteration": i
            }
        }
        
        try:
            response = requests.post(f"{API_URL}/log_data", json=payload, timeout=2)
            if response.status_code == 200:
                print(f"  ✅ Batch {i+1}: Sent {len(alerts)} alerts - Score: {score}")
                if alerts:
                    print(f"     Alerts: {', '.join(alerts)}")
            else:
                print(f"  ❌ Batch {i+1}: Failed - {response.status_code}")
        except Exception as e:
            print(f"  ❌ Batch {i+1}: Error - {e}")
        
        time.sleep(2)  # Wait 2 seconds between batches
    
    print(f"\n✅ Test data sent for session {session_id}")
    print(f"Check: {API_URL}/api/debug/session/{session_id}")

if __name__ == "__main__":
    session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    student_id = "NEGA"
    
    send_test_data(session_id, student_id)