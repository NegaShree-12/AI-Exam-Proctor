# websocket_manager.py
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import json

# Store active sessions
active_sessions = {}
proctor_rooms = {}

def init_socketio(app):
    """Initialize SocketIO with the Flask app"""
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
    
    @socketio.on('connect')
    def handle_connect():
        print(f'[WebSocket] Client connected: {request.sid}')
    
    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'[WebSocket] Client disconnected: {request.sid}')
        # Remove from active sessions
        for student_id, session_data in list(active_sessions.items()):
            if session_data.get('sid') == request.sid:
                del active_sessions[student_id]
                # Notify proctors
                emit('student_disconnected', {
                    'student_id': student_id,
                    'session_id': session_data.get('session_id')
                }, room='proctors', broadcast=True)
                break
    
    @socketio.on('proctor_join')
    def handle_proctor_join(data):
        """Proctor joins to monitor all sessions"""
        join_room('proctors')
        proctor_rooms[request.sid] = 'proctors'
        
        # Send all active sessions to the proctor
        emit('active_sessions_list', {
            'sessions': list(active_sessions.values())
        })
        print(f'[WebSocket] Proctor joined: {request.sid}')
    
    @socketio.on('student_join')
    def handle_student_join(data):
        """Student starts exam session"""
        student_id = data.get('student_id')
        session_id = data.get('session_id')
        exam_id = data.get('exam_id')
        
        # Store student session
        active_sessions[student_id] = {
            'sid': request.sid,
            'student_id': student_id,
            'session_id': session_id,
            'exam_id': exam_id,
            'joined_at': datetime.now().isoformat(),
            'last_alert': None,
            'alert_count': 0,
            'risk_level': 'LOW',
            'alerts_history': []
        }
        
        # Notify proctors
        emit('student_joined', {
            'student_id': student_id,
            'session_id': session_id,
            'exam_id': exam_id,
            'joined_at': active_sessions[student_id]['joined_at']
        }, room='proctors')
        
        print(f'[WebSocket] Student joined: {student_id} - Session: {session_id}')
    
    @socketio.on('live_alert')
    def handle_live_alert(data):
        """Receive real-time alerts from student client"""
        student_id = data.get('student_id')
        session_id = data.get('session_id')
        alert = data.get('alert')
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        if student_id in active_sessions:
            # Update session data
            active_sessions[student_id]['last_alert'] = {
                'alert': alert,
                'timestamp': timestamp
            }
            active_sessions[student_id]['alert_count'] += 1
            
            # Calculate risk level
            alert_count = active_sessions[student_id]['alert_count']
            if alert_count > 10:
                risk_level = 'HIGH'
            elif alert_count > 5:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            active_sessions[student_id]['risk_level'] = risk_level
            
            # Add to history (keep last 10)
            history = active_sessions[student_id].get('alerts_history', [])
            history.append({
                'alert': alert,
                'timestamp': timestamp
            })
            active_sessions[student_id]['alerts_history'] = history[-10:]
            
            # Broadcast to all proctors
            emit('new_alert', {
                'student_id': student_id,
                'session_id': session_id,
                'alert': alert,
                'timestamp': timestamp,
                'alert_count': active_sessions[student_id]['alert_count'],
                'risk_level': risk_level
            }, room='proctors')
            
            print(f'[WebSocket] Alert from {student_id}: {alert}')
    
    @socketio.on('proctor_message')
    def handle_proctor_message(data):
        """Proctor sends message to specific student"""
        student_id = data.get('student_id')
        message = data.get('message')
        
        if student_id in active_sessions:
            student_sid = active_sessions[student_id]['sid']
            emit('proctor_warning', {
                'message': message,
                'timestamp': datetime.now().isoformat()
            }, room=student_sid)
            
            print(f'[WebSocket] Proctor message to {student_id}: {message}')
    
    return socketio