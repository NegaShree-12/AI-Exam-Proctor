from flask import Flask, request, jsonify, send_file, after_this_request, Response
from flask_cors import CORS
from flask_socketio import SocketIO
import sqlite3
import json
import os
import pandas as pd
from report_generator import generate_report
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import time
import eventlet
import uuid
eventlet.monkey_patch()

# Import WebSocket manager
from websocket_manager import init_socketio

# Import Analytics Engine
from analytics_engine import AnalyticsEngine
import csv
from io import StringIO

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Memory limits
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['PROPAGATE_EXCEPTIONS'] = True

# Initialize SocketIO
socketio = init_socketio(app)

# Initialize Analytics Engine
analytics_engine = AnalyticsEngine()

DATABASE_FILE = 'proctoring_data.db'

# Store active client sessions
active_client_sessions = {}  # session_token -> {username, exam_id, status, last_heartbeat}

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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'admin'))
    );
    """)
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
# 🔹 CLIENT SESSION MANAGEMENT
# ===================================================

@app.route('/api/start-client-session', methods=['POST'])
def start_client_session():
    """Generate session token for client download and launch"""
    try:
        data = request.json
        username = data.get('username')
        exam_id = data.get('exam_id')
        
        if not username or not exam_id:
            return jsonify({"error": "Missing username or exam_id"}), 400
        
        # Generate unique session token
        session_token = str(uuid.uuid4())
        session_id = f"exam_{exam_id}_{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store session info
        active_client_sessions[session_token] = {
            'username': username,
            'exam_id': exam_id,
            'session_id': session_id,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'last_heartbeat': None
        }
        
        # Generate download URL and command
        if os.name == 'nt':  # Windows
            client_filename = 'ProctorAI.exe'
            run_command = f'.\\{client_filename} --username {username} --exam_id {exam_id} --token {session_token}'
        else:  # Mac/Linux
            client_filename = 'ProctorAI'
            run_command = f'./{client_filename} --username {username} --exam_id {exam_id} --token {session_token}'
        
        download_url = f"{request.host_url}api/download-client/{client_filename}"
        
        return jsonify({
            'success': True,
            'session_token': session_token,
            'session_id': session_id,
            'download_url': download_url,
            'command': run_command,
            'client_filename': client_filename
        })
        
    except Exception as e:
        print(f"Error starting client session: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/check-client-status/<session_token>', methods=['GET'])
def check_client_status(session_token):
    """Check if client has connected"""
    if session_token in active_client_sessions:
        session = active_client_sessions[session_token]
        return jsonify({
            'status': session['status'],
            'session_id': session.get('session_id'),
            'connected_at': session.get('last_heartbeat'),
            'username': session['username'],
            'exam_id': session['exam_id']
        })
    return jsonify({'status': 'not_found'}), 404

@app.route('/api/client-heartbeat', methods=['POST'])
def client_heartbeat():
    """Client sends heartbeat to confirm it's running"""
    try:
        data = request.json
        session_token = data.get('session_token')
        username = data.get('username')
        exam_id = data.get('exam_id')
        
        if session_token in active_client_sessions:
            active_client_sessions[session_token]['status'] = 'active'
            active_client_sessions[session_token]['last_heartbeat'] = datetime.now().isoformat()
            active_client_sessions[session_token]['session_id'] = data.get('session_id')
            
            # Notify via WebSocket
            socketio.emit('client_connected', {
                'username': username,
                'exam_id': exam_id,
                'session_token': session_token
            }, room='proctors')
            
            return jsonify({'status': 'ok'})
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
    except Exception as e:
        print(f"Heartbeat error: {e}")
        return jsonify({'status': 'error'}), 500

@app.route('/api/download-client/<filename>', methods=['GET'])
def download_client(filename):
    """Serve the client executable or redirect to GitHub"""
    try:
        # First try to serve from local folder
        client_path = os.path.join(os.path.dirname(__file__), 'client_binaries', filename)
        
        if os.path.exists(client_path):
            return send_file(
                client_path,
                as_attachment=True,
                download_name=filename,
                mimetype='application/octet-stream'
            )
        else:
            # If file doesn't exist locally, redirect to GitHub release
            github_url = f"https://github.com/vishwas2222/ProctorAI-Plus/releases/download/v1.0.0/{filename}"
            print(f"[Download] Redirecting to GitHub: {github_url}")
            
            # Return a redirect response
            return redirect(github_url, code=302)
            
    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({
            "error": "Download failed",
            "message": "Please download manually from GitHub",
            "download_url": f"https://github.com/vishwas2222/ProctorAI-Plus/releases/download/v1.0.0/{filename}"
        }), 500

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
            MAX(e.integrity_score) as final_score
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
            e.id as exam_id, e.title, e.description, a.status, a.assigned_at
        FROM exam_assignments a
        JOIN exams e ON a.exam_id = e.id
        WHERE a.student_id = ?
        ORDER BY a.assigned_at DESC
    """, (student_id,))
    exams = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(exams)

# ===================================================
# 🔹 PROCTORING DATA ENDPOINT
# ===================================================
@app.route('/log_data', methods=['POST'])
def log_data():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        is_web_alert = data.get('source') == 'web'
        student_id = data.get('student_id')
        session_id = data.get('session_id')
        
        if not student_id or not session_id:
            return jsonify({"status": "error", "message": "student_id and session_id are required"}), 400

        current_alerts_list = data.get('alerts', [])
        if not isinstance(current_alerts_list, list):
            current_alerts_list = []
        current_alerts_set = set(current_alerts_list)

        last_alerts_set = SESSION_LAST_ALERTS.get(session_id, set())
        if not is_web_alert and current_alerts_set == last_alerts_set:
            return jsonify({"status": "success", "message": "No change"}), 200

        SESSION_LAST_ALERTS[session_id] = current_alerts_set

        if is_web_alert:
            metrics = {"source": "web"}
            timestamp = datetime.utcnow().isoformat() + "Z"
        else:
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
        
        if not current_alerts_list:
            SESSION_LAST_ALERTS.pop(session_id, None)
            
        return jsonify({"status": "success", "message": "Data logged"}), 200
        
    except Exception as e:
        print(f"Error in log_data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ===================================================
# 🔹 LIVE MONITORING ENDPOINTS
# ===================================================
@app.route('/log_live_alert', methods=['POST'])
def log_live_alert():
    try:
        data = request.get_json()
        
        socketio.emit('new_alert', {
            'student_id': data.get('student_id'),
            'session_id': data.get('session_id'),
            'alert': data.get('alert'),
            'timestamp': datetime.utcnow().isoformat() + "Z"
        }, room='proctors')
        
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print(f"Error in live alert: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/api/active_sessions', methods=['GET'])
def get_active_sessions():
    from websocket_manager import active_sessions
    return jsonify(list(active_sessions.values()))

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

@app.route('/api/analytics/charts/<session_id>', methods=['GET'])
def get_session_charts(session_id):
    try:
        analytics = analytics_engine.get_session_analytics(session_id)
        if analytics:
            charts = analytics_engine.generate_charts(analytics, type='session')
            return jsonify(charts)
        return jsonify({"error": "Session not found"}), 404
    except Exception as e:
        print(f"Chart generation error: {e}")
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
@app.route('/get_sessions/<student_id>', methods=['GET'])
def get_sessions(student_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT session_id FROM events WHERE student_id = ? ORDER BY session_id DESC", (student_id,))
    sessions = [row[0] for row in cursor.fetchall()]
    conn.close()
    return jsonify(sessions)

@app.route('/get_data/<student_id>/<session_id>', methods=['GET'])
def get_data(student_id, session_id):
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE student_id = ? AND session_id = ? ORDER BY timestamp DESC", (student_id, session_id))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(rows)

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

if __name__ == '__main__':
    init_db()
    
    # Create client_binaries directory if it doesn't exist
    os.makedirs('client_binaries', exist_ok=True)
    
    print("Starting server with WebSocket and Analytics support...")
    print("✅ Phase 1: Live Monitoring Active")
    print("✅ Phase 2: Analytics Engine Ready")
    print("✅ Phase 3: Auto-Launch Support Active")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)