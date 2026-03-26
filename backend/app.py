from flask import Flask, request, jsonify, send_file, after_this_request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, join_room
import sqlite3
import json
import os
import pandas as pd
from report_generator import generate_report
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid
import subprocess
import psutil
import signal
import sys

# Import Analytics Engine
from analytics_engine import AnalyticsEngine
import csv
from io import StringIO

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Memory limits
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['PROPAGATE_EXCEPTIONS'] = True

# Initialize SocketIO WITHOUT eventlet
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Analytics Engine
analytics_engine = AnalyticsEngine()

DATABASE_FILE = 'proctoring_data.db'

# Store active web sessions (for live monitoring)
active_web_sessions = {}  # session_id -> {student_id, exam_id, last_heartbeat, alerts}

# Store background agent processes
active_agent_sessions = {}  # session_id -> {pid, username, exam_id, started_at}

ALERT_WEIGHTS = {
    "Multiple faces detected!": 25,
    "CELL PHONE detected!": 20,
    "LAPTOP detected!": 20,
    "BOOK detected!": 15,
    "No person detected!": 15,
    "Someone is talking!": 5,
    "VOICE:": 10,
    "Suspicious micro gesture detected!": 5,
    "Hand on mouse/keyboard detected!": 2,
    "WEB: Switched tabs": 8,
    "WEB: Left focus": 5
}

SESSION_LAST_ALERTS = {}

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Flask backend running successfully"}), 200

def calculate_integrity_score(alerts):
    score = 100
    if not alerts: 
        return score
    
    # Higher weights for serious violations
    SERIOUS_WEIGHTS = {
        "CELL PHONE detected!": 40,
        "Multiple faces detected!": 40,
        "LAPTOP detected!": 35,
        "BOOK detected!": 30,
        "No person detected!": 25,
        "Someone is talking!": 10,
        "VOICE:": 15,
        "WEB: Switched tabs": 10,
        "WEB: Left focus": 8
    }
    
    for alert in set(alerts):
        for key, weight in SERIOUS_WEIGHTS.items():
            if key in alert:
                score -= weight
                break
    
    serious_count = sum(1 for a in alerts if any(
        s in a for s in ["CELL PHONE", "Multiple faces", "LAPTOP", "BOOK"]
    ))
    
    if serious_count > 1:
        score -= serious_count * 5
    
    return max(0, score)

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'admin'))
    );
    """)
    
    # Events table for proctoring data
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        session_id TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        alerts TEXT,
        metrics TEXT,
        integrity_score REAL
    );
    """)
    
    # Exams table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        created_by_admin_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by_admin_id) REFERENCES users (id)
    );
    """)
    
    # Exam assignments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exam_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'assigned',
        assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (exam_id) REFERENCES exams (id),
        FOREIGN KEY (student_id) REFERENCES users (id),
        UNIQUE(exam_id, student_id)
    );
    """)
    
    conn.commit()
    conn.close()
    print("SQLite database is ready.")

# ===================================================
# 🔹 AUTH ENDPOINTS
# ===================================================
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    if not username or not password or not role:
        return jsonify({"status": "error", "message": "Missing username, password, or role"}), 400
    
    if role not in ['student', 'admin']:
        return jsonify({"status": "error", "message": "Role must be 'student' or 'admin'"}), 400
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "message": "Username already exists"}), 409
    
    password_hash = generate_password_hash(password)
    sql = "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)"
    cursor.execute(sql, (username, password_hash, role))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"status": "error", "message": "Missing username or password"}), 400
    
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user or not check_password_hash(user['password_hash'], password):
        conn.close()
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401
    
    conn.close()
    return jsonify({
        "status": "success",
        "message": "Login successful",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "role": user['role']
        }
    }), 200

# ===================================================
# 🔹 ADMIN API ENDPOINTS
# ===================================================
@app.route('/api/students', methods=['GET'])
def get_students():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE role = 'student'")
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(students)

@app.route('/api/exams', methods=['GET', 'POST'])
def handle_exams():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    
    if request.method == 'POST':
        data = request.json
        title = data.get('title')
        description = data.get('description')
        admin_id = data.get('admin_id')
        
        if not title or not admin_id:
            return jsonify({"status": "error", "message": "Missing title or admin_id"}), 400
        
        cursor = conn.cursor()
        sql = "INSERT INTO exams (title, description, created_by_admin_id) VALUES (?, ?, ?)"
        cursor.execute(sql, (title, description, admin_id))
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Exam created successfully"}), 201
    
    elif request.method == 'GET':
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.title, e.description, e.created_at, u.username as admin_username
            FROM exams e
            JOIN users u ON e.created_by_admin_id = u.id
            ORDER BY e.created_at DESC
        """)
        exams = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(exams)

@app.route('/api/assign', methods=['POST'])
def assign_exam():
    data = request.json
    exam_id = data.get('exam_id')
    student_id = data.get('student_id')
    
    if not exam_id or not student_id:
        return jsonify({"status": "error", "message": "Missing exam_id or student_id"}), 400
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        sql = "INSERT INTO exam_assignments (exam_id, student_id) VALUES (?, ?)"
        cursor.execute(sql, (exam_id, student_id))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"status": "error", "message": "This exam is already assigned to this student"}), 409
    
    conn.close()
    return jsonify({"status": "success", "message": "Exam assigned successfully"}), 201

@app.route('/api/exam_details/<int:exam_id>', methods=['GET'])
def get_exam_details(exam_id):
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description FROM exams WHERE id = ?", (exam_id,))
    exam = cursor.fetchone()
    
    if not exam:
        conn.close()
        return jsonify({"status": "error", "message": "Exam not found"}), 404
    
    conn.close()
    return jsonify(dict(exam))

@app.route('/api/exam_sessions/<int:exam_id>', methods=['GET'])
def get_sessions_for_exam(exam_id):
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all students assigned to this exam
    cursor.execute("""
        SELECT u.username 
        FROM exam_assignments a
        JOIN users u ON a.student_id = u.id
        WHERE a.exam_id = ?
    """, (exam_id,))
    students = cursor.fetchall()
    
    if not students:
        conn.close()
        return jsonify([])
    
    student_usernames = [s['username'] for s in students]
    placeholders = ','.join('?' for _ in student_usernames)
    
    query = f"""
        SELECT 
            e.session_id, 
            e.student_id as student_username, 
            MIN(e.timestamp) as start_time, 
            MAX(e.integrity_score) as final_score,
            COUNT(*) as event_count
        FROM events e
        WHERE e.student_id IN ({placeholders}) 
        AND e.session_id LIKE ?
        GROUP BY e.session_id, e.student_id
        ORDER BY start_time DESC
    """
    
    params = student_usernames + [f'%exam_{exam_id}%']
    cursor.execute(query, params)
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(sessions)

# ===================================================
# 🔹 STUDENT API ENDPOINTS
# ===================================================
@app.route('/api/my_exams/<int:student_id>', methods=['GET'])
def get_student_exams(student_id):
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            e.id as exam_id, 
            e.title, 
            e.description, 
            a.status, 
            a.assigned_at
        FROM exam_assignments a
        JOIN exams e ON a.exam_id = e.id
        WHERE a.student_id = ?
        ORDER BY a.assigned_at DESC
    """, (student_id,))
    exams = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(exams)

# ===================================================
# 🔹 BACKGROUND AGENT ENDPOINTS
# ===================================================

@app.route('/api/launch-background-agent', methods=['POST'])
def launch_background_agent():
    """Launch the proctoring agent in background mode (no window)"""
    try:
        data = request.json
        username = data.get('username')
        exam_id = data.get('exam_id')
        session_id = data.get('session_id')
        
        if not all([username, exam_id, session_id]):
            return jsonify({"error": "Missing parameters"}), 400
        
        # Path to your existing main.py
        script_path = os.path.join(os.path.dirname(__file__), '..', 'client-agent', 'main.py')
        
        # If script doesn't exist, try alternate path
        if not os.path.exists(script_path):
            script_path = os.path.join(os.getcwd(), 'client-agent', 'main.py')
        
        # Check if script exists
        if not os.path.exists(script_path):
            print(f"⚠️ Agent script not found at: {script_path}")
            # For testing, we'll simulate success
            return jsonify({
                'success': True,
                'message': 'Simulation mode - agent script not found',
                'simulation': True
            }), 200
        
        # Launch Python script in background with --background flag
        if sys.platform == 'win32':
            # Windows - hide window completely
            process = subprocess.Popen(
                [sys.executable, script_path, 
                 '--username', username, 
                 '--exam_id', str(exam_id),
                 '--session_id', session_id,
                 '--background',  # This makes it run with NO WINDOW
                 '--no-yolo'],  # Add --no-yolo for faster startup if needed
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
        else:
            # Linux/Mac
            process = subprocess.Popen(
                [sys.executable, script_path,
                 '--username', username,
                 '--exam_id', str(exam_id),
                 '--session_id', session_id,
                 '--background',
                 '--no-yolo'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        
        # Store process info
        active_agent_sessions[session_id] = {
            'pid': process.pid,
            'username': username,
            'exam_id': exam_id,
            'started_at': datetime.now().isoformat()
        }
        
        print(f"✅ Background agent launched for {username} (PID: {process.pid})")
        
        return jsonify({
            'success': True,
            'pid': process.pid,
            'message': 'Background agent launched'
        })
        
    except Exception as e:
        print(f"❌ Error launching agent: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stop-background-agent/<session_id>', methods=['POST'])
def stop_background_agent(session_id):
    """Stop the background proctoring agent"""
    try:
        if session_id in active_agent_sessions:
            pid = active_agent_sessions[session_id]['pid']
            
            # Kill the process
            try:
                if sys.platform == 'win32':
                    subprocess.run(['taskkill', '/F', '/PID', str(pid)], 
                                 capture_output=True, timeout=5)
                else:
                    os.kill(pid, signal.SIGTERM)
                
                print(f"✅ Stopped agent (PID: {pid})")
            except Exception as e:
                print(f"⚠️ Error killing process: {e}")
            
            del active_agent_sessions[session_id]
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'Session not found'}), 404
        
    except Exception as e:
        print(f"❌ Error stopping agent: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/check-agent-status/<session_id>', methods=['GET'])
def check_agent_status(session_id):
    """Check if background agent is running"""
    try:
        if session_id in active_agent_sessions:
            pid = active_agent_sessions[session_id]['pid']
            if psutil.pid_exists(pid):
                return jsonify({'status': 'running'})
            else:
                # Clean up if process died
                del active_agent_sessions[session_id]
                return jsonify({'status': 'stopped'})
        
        # For testing/simulation, return not found
        return jsonify({'status': 'not_found'}), 404
    except Exception as e:
        print(f"Error checking status: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ===================================================
# 🔹 WEB PROCTORING ENDPOINTS
# ===================================================

@app.route('/api/start-web-session', methods=['POST'])
def start_web_session():
    """Start a web-based proctoring session"""
    try:
        data = request.json
        username = data.get('username')
        exam_id = data.get('exam_id')
        
        if not username or not exam_id:
            return jsonify({"error": "Missing username or exam_id"}), 400
        
        # Generate session ID
        session_id = f"exam_{exam_id}_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store session info
        active_web_sessions[session_id] = {
            'username': username,
            'exam_id': exam_id,
            'session_id': session_id,
            'status': 'active',
            'started_at': datetime.now().isoformat(),
            'last_heartbeat': datetime.now().isoformat(),
            'alerts': []
        }
        
        # Log exam start
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO events (student_id, session_id, timestamp, alerts, metrics, integrity_score) VALUES (?, ?, ?, ?, ?, ?)",
            (username, session_id, datetime.utcnow().isoformat() + "Z", json.dumps(["Exam started"]), json.dumps({"source": "web"}), 100)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"Error starting web session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/web-heartbeat', methods=['POST'])
def web_heartbeat():
    """Web client sends heartbeat"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id in active_web_sessions:
            active_web_sessions[session_id]['last_heartbeat'] = datetime.now().isoformat()
            return jsonify({'status': 'ok'})
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    except Exception as e:
        print(f"Heartbeat error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/api/end-web-session', methods=['POST'])
def end_web_session():
    """End a web proctoring session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if session_id in active_web_sessions:
            del active_web_sessions[session_id]
            
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error ending session: {e}")
        return jsonify({'error': str(e)}), 500

# ===================================================
# 🔹 PROCTORING DATA ENDPOINT
# ===================================================
@app.route('/log_data', methods=['POST'])
def log_data():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        source = data.get('source', 'web')
        student_id = data.get('student_id')
        session_id = data.get('session_id')
        
        if not student_id or not session_id:
            return jsonify({"status": "error", "message": "student_id and session_id are required"}), 400

        current_alerts_list = data.get('alerts', [])
        if not isinstance(current_alerts_list, list):
            current_alerts_list = []
        
        current_alerts_set = set(current_alerts_list)
        last_alerts_set = SESSION_LAST_ALERTS.get(session_id, set())
        
        # Only log if alerts changed or it's from web
        if source == 'web' or current_alerts_set != last_alerts_set:
            SESSION_LAST_ALERTS[session_id] = current_alerts_set

            metrics = data.get('metrics', {})
            timestamp = data.get('timestamp', datetime.utcnow().isoformat() + "Z")

            score = calculate_integrity_score(current_alerts_list)
            
            if len(current_alerts_list) > 10:
                current_alerts_list = current_alerts_list[:10]
                
            alerts_json = json.dumps(current_alerts_list)
            metrics_json = json.dumps(metrics)

            conn = sqlite3.connect(DATABASE_FILE, timeout=10)
            cursor = conn.cursor()
            sql = "INSERT INTO events (student_id, session_id, timestamp, alerts, metrics, integrity_score) VALUES (?, ?, ?, ?, ?, ?)"
            cursor.execute(sql, (student_id, session_id, timestamp, alerts_json, metrics_json, score))
            conn.commit()
            conn.close()
            
            # Update active session
            if session_id in active_web_sessions:
                if current_alerts_list:
                    active_web_sessions[session_id]['alerts'].extend(current_alerts_list)
                    # Keep last 10 alerts
                    active_web_sessions[session_id]['alerts'] = active_web_sessions[session_id]['alerts'][-10:]
            
            # Emit via WebSocket for live monitoring
            for alert in current_alerts_list:
                socketio.emit('new_alert', {
                    'student_id': student_id,
                    'session_id': session_id,
                    'alert': alert,
                    'timestamp': timestamp
                })
            
            return jsonify({"status": "success", "message": "Data logged"}), 200
        
        return jsonify({"status": "success", "message": "No change"}), 200
        
    except Exception as e:
        print(f"Error in log_data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ===================================================
# 🔹 LIVE MONITORING ENDPOINTS
# ===================================================
@app.route('/api/active_sessions', methods=['GET'])
def get_active_sessions():
    """Get all active web proctoring sessions"""
    sessions_list = []
    for session_id, data in active_web_sessions.items():
        sessions_list.append({
            'student_id': data['username'],
            'session_id': session_id,
            'exam_id': data['exam_id'],
            'started_at': data['started_at'],
            'last_heartbeat': data['last_heartbeat'],
            'alert_count': len(data['alerts']),
            'recent_alerts': data['alerts'][-5:] if data['alerts'] else []
        })
    return jsonify(sessions_list)

# ===================================================
# 🔹 ANALYTICS ENDPOINTS
# ===================================================
@app.route('/api/analytics/session/<session_id>', methods=['GET'])
def get_session_analytics(session_id):
    try:
        analytics = analytics_engine.get_session_analytics(session_id)
        if analytics:
            return jsonify(analytics)
        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics/exam/<int:exam_id>', methods=['GET'])
def get_exam_analytics(exam_id):
    try:
        analytics = analytics_engine.get_exam_analytics(exam_id)
        if analytics:
            return jsonify(analytics)
        return jsonify({"error": "No data found for exam"}), 404
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({"error": str(e)}), 500

# ===================================================
# 🔹 EXPORT ENDPOINTS
# ===================================================
@app.route('/api/export/session/<session_id>', methods=['GET'])
def export_session_data(session_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        query = "SELECT * FROM events WHERE session_id = ? ORDER BY timestamp"
        df = pd.read_sql_query(query, conn, params=(session_id,))
        conn.close()
        
        if df.empty:
            return jsonify({"error": "No data found"}), 404
        
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return Response(
            csv_buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={session_id}_data.csv"}
        )
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/exam/<int:exam_id>', methods=['GET'])
def export_exam_data(exam_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        query = "SELECT * FROM events WHERE session_id LIKE ? ORDER BY timestamp"
        df = pd.read_sql_query(query, conn, params=(f'%exam_{exam_id}%',))
        conn.close()
        
        if df.empty:
            return jsonify({"error": "No data found"}), 404
        
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        
        return Response(
            csv_buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=exam_{exam_id}_data.csv"}
        )
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500

# ===================================================
# 🔹 REPORTING ENDPOINTS
# ===================================================
@app.route('/generate_report/<student_id>/<session_id>', methods=['GET'])
def download_report(student_id, session_id):
    SESSION_LAST_ALERTS.pop(session_id, None)
    
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp_reports')
    os.makedirs(temp_dir, exist_ok=True)
    report_filename = f"Report_{student_id}_{session_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    report_path = os.path.join(temp_dir, report_filename)

    print(f"Generating report at: {report_path}")
    generated_file_path = generate_report(student_id, session_id, report_path)

    if generated_file_path:
        @after_this_request
        def remove_file(response):
            try:
                os.remove(generated_file_path)
            except Exception as error:
                app.logger.error(f"Error removing file: {error}")
            return response

        return send_file(
            generated_file_path,
            as_attachment=True,
            download_name=f"Report_{student_id}_{session_id}.pdf"
        )
    else:
        return "Could not generate report: No data for this session.", 404

# ===================================================
# 🔹 FALLBACK FOR TESTING - SIMULATE AGENT
# ===================================================

@app.route('/api/simulate-agent-start/<session_id>', methods=['POST'])
def simulate_agent_start(session_id):
    """For testing: manually mark an agent as running"""
    try:
        data = request.json
        username = data.get('username', 'test')
        exam_id = data.get('exam_id', '1')
        
        active_agent_sessions[session_id] = {
            'pid': 12345,  # Fake PID
            'username': username,
            'exam_id': exam_id,
            'started_at': datetime.now().isoformat()
        }
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/test-alert', methods=['POST'])
def test_alert():
    """Test endpoint to manually add an alert"""
    try:
        data = request.json
        student_id = data.get('student_id')
        session_id = data.get('session_id')
        alert = data.get('alert')
        
        if not all([student_id, session_id, alert]):
            return jsonify({"error": "Missing parameters"}), 400
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Calculate a lower score for test alerts
        score = 50
        
        cursor.execute(
            "INSERT INTO events (student_id, session_id, timestamp, alerts, metrics, integrity_score) VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, session_id, datetime.utcnow().isoformat() + "Z", 
             json.dumps([alert]), json.dumps({"test": True, "source": "test_endpoint"}), score)
        )
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": f"Alert '{alert}' added", "score": score})
    except Exception as e:
        print(f"Error in test-alert: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/api/debug/all-sessions', methods=['GET'])
def debug_all_sessions():
    """Debug endpoint to see all sessions"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all distinct sessions with summary
        cursor.execute("""
            SELECT 
                session_id, 
                student_id,
                COUNT(*) as event_count,
                MIN(timestamp) as start_time,
                MAX(timestamp) as end_time,
                AVG(integrity_score) as avg_score,
                MIN(integrity_score) as min_score
            FROM events 
            GROUP BY session_id, student_id
            ORDER BY start_time DESC
            LIMIT 20
        """)
        
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'total_sessions': len(sessions),
            'sessions': sessions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug/session/<session_id>', methods=['GET'])
def debug_session(session_id):
    """Debug endpoint to see raw data for a session"""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all events for this session
        cursor.execute("""
            SELECT id, student_id, session_id, timestamp, alerts, metrics, integrity_score
            FROM events 
            WHERE session_id = ?
            ORDER BY timestamp
        """, (session_id,))
        
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Parse JSON fields for display
        for event in events:
            if event.get('alerts'):
                try:
                    event['alerts'] = json.loads(event['alerts'])
                except:
                    pass
            if event.get('metrics'):
                try:
                    event['metrics'] = json.loads(event['metrics'])
                except:
                    pass
        
        return jsonify({
            'session_id': session_id,
            'total_events': len(events),
            'events': events
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# ===================================================
# 🔹 WEBSOCKET EVENTS
# ===================================================
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_proctor')
def handle_join_proctor():
    """Proctor joins to monitor sessions"""
    join_room('proctors')
    print(f'Proctor joined: {request.sid}')

if __name__ == '__main__':
    init_db()
    
    print("="*60)
    print("🚀 ProctorAI+ Backend Starting...")
    print("="*60)
    print("✅ Database initialized")
    print("✅ Analytics Engine Ready")
    print("✅ WebSocket Server Ready")
    print("✅ Background Agent Support Enabled")
    print("="*60)
    print("📡 Server running on http://localhost:5000")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)