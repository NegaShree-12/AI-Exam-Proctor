# test_alerts.py
import requests
import json

API_URL = "http://127.0.0.1:5000"

def send_test_alert(student_id, session_id, alert):
    """Send a test alert to the backend"""
    try:
        response = requests.post(
            f"{API_URL}/api/test-alert",
            json={
                "student_id": student_id,
                "session_id": session_id,
                "alert": alert
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alert sent: {alert}")
            print(f"   Score: {data.get('score')}")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_multiple_alerts():
    """Test sending multiple alerts"""
    session_id = input("Enter session ID: ").strip()
    student_id = input("Enter student username: ").strip()
    
    if not session_id or not student_id:
        print("Session ID and student ID required")
        return
    
    alerts = [
        "Multiple faces detected!",
        "CELL PHONE detected!",
        "Someone is talking!",
        "No person detected!",
        "LAPTOP detected!"
    ]
    
    print(f"\nSending {len(alerts)} test alerts...")
    for alert in alerts:
        send_test_alert(student_id, session_id, alert)
        import time
        time.sleep(1)
    
    print(f"\n✅ All alerts sent!")
    print(f"Check debug endpoint: {API_URL}/api/debug/session/{session_id}")

if __name__ == "__main__":
    test_multiple_alerts()