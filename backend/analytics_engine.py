# backend/analytics_engine.py
import sqlite3
import json
from datetime import datetime
from collections import Counter
import math

DATABASE_FILE = 'proctoring_data.db'

class AnalyticsEngine:
    def __init__(self):
        self.alert_weights = {
            "Multiple faces detected!": 25,
            "CELL PHONE detected!": 20,
            "LAPTOP detected!": 20,
            "BOOK detected!": 15,
            "No person detected!": 15,
            "Someone is talking!": 5,
            "VOICE:": 10,
            "WEB: Switched tabs": 8,
            "WEB: Left focus": 5
        }
    
    def get_session_analytics(self, session_id):
        """Get detailed analytics for a specific session"""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get all events for this session
        cursor.execute("""
            SELECT student_id, timestamp, alerts, metrics, integrity_score 
            FROM events 
            WHERE session_id = ? 
            ORDER BY timestamp ASC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
        
        # Process data
        student_id = rows[0][0]
        timestamps = []
        alerts_list = []
        scores = []
        
        for row in rows:
            timestamps.append(row[1])
            try:
                alerts = json.loads(row[2]) if row[2] else []
            except:
                alerts = []
            alerts_list.append(alerts)
            scores.append(row[4] if row[4] else 100)
        
        # Calculate duration
        if len(timestamps) >= 2:
            try:
                start = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
                end = datetime.fromisoformat(timestamps[-1].replace('Z', '+00:00'))
                duration_min = round((end - start).total_seconds() / 60, 2)
            except:
                duration_min = 0
        else:
            duration_min = 0
        
        # Count unique alerts
        all_alerts = []
        for alerts in alerts_list:
            all_alerts.extend(alerts)
        
        alert_counts = Counter(all_alerts)
        unique_alerts = [{'alert': k, 'count': v} for k, v in alert_counts.most_common()]
        
        # Create timeline
        alert_timeline = []
        score_timeline = []
        
        for i, timestamp in enumerate(timestamps):
            try:
                time_str = timestamp[11:19] if len(timestamp) > 19 else timestamp
            except:
                time_str = str(i)
            
            if i < len(alerts_list) and i < len(scores):
                alert_timeline.append({
                    'time': time_str,
                    'alerts': alerts_list[i],
                    'score': scores[i]
                })
                score_timeline.append({
                    'time': time_str,
                    'score': scores[i]
                })
        
        # Calculate risk distribution
        total = len(scores)
        if total > 0:
            low_risk = len([s for s in scores if s >= 80]) / total * 100
            medium_risk = len([s for s in scores if 60 <= s < 80]) / total * 100
            high_risk = len([s for s in scores if s < 60]) / total * 100
        else:
            low_risk = medium_risk = high_risk = 0
        
        # Alert frequency
        if duration_min > 0:
            alert_frequency = len(all_alerts) / duration_min
        else:
            alert_frequency = 0
        
        # Find peak risk times (lowest scores)
        peak_times = []
        if len(scores) >= 5:
            # Group into chunks
            chunk_size = max(1, len(scores) // 5)
            for i in range(0, len(scores), chunk_size):
                chunk_scores = scores[i:i+chunk_size]
                if chunk_scores:
                    avg_score = sum(chunk_scores) / len(chunk_scores)
                    time_idx = i + len(chunk_scores)//2
                    if time_idx < len(timestamps):
                        time_str = timestamps[time_idx][11:16] if len(timestamps[time_idx]) > 16 else str(time_idx)
                        peak_times.append({
                            'time': time_str,
                            'avg_score': round(avg_score, 1)
                        })
            # Sort by lowest score and take top 3
            peak_times = sorted(peak_times, key=lambda x: x['avg_score'])[:3]
        
        # Calculate stats
        if scores:
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            
            # Calculate standard deviation
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            std_score = math.sqrt(variance) if variance > 0 else 0
        else:
            avg_score = min_score = max_score = std_score = 0
        
        # Check if terminated
        terminated = any("EXAM_TERMINATED" in str(alerts) for alerts in alerts_list)
        
        integrity_stats = {
            'avg_score': round(avg_score, 1),
            'min_score': round(min_score, 1),
            'max_score': round(max_score, 1),
            'std_score': round(std_score, 1),
            'final_score': round(scores[-1], 1) if scores else 0,
            'terminated': terminated
        }
        
        # Generate summary
        if terminated:
            integrity_level = "FAILED - Exam Terminated"
            recommendation = "Exam was automatically terminated due to serious violation"
            risk_level = "HIGH"
        elif avg_score >= 90:
            integrity_level = "Excellent"
            recommendation = "No action needed"
            risk_level = "LOW"
        elif avg_score >= 80:
            integrity_level = "Good"
            recommendation = "Minor review recommended"
            risk_level = "LOW"
        elif avg_score >= 70:
            integrity_level = "Fair"
            recommendation = "Manual review required"
            risk_level = "MEDIUM"
        else:
            integrity_level = "Poor"
            recommendation = "Serious concerns - investigate thoroughly"
            risk_level = "HIGH"
        
        serious_violations = [a for a in all_alerts if any(
            s in a for s in ["PHONE", "Multiple faces", "BOOK", "LAPTOP", "EXAM_TERMINATED"]
        )]
        
        summary = {
            'integrity_level': integrity_level,
            'recommendation': recommendation,
            'total_alerts': len(all_alerts),
            'serious_violations': len(serious_violations),
            'violation_types': list(set(serious_violations))[:5],
            'risk_level': risk_level,
            'terminated': terminated
        }
        
        return {
            'session_id': session_id,
            'student_id': student_id,
            'duration': duration_min,
            'total_events': len(rows),
            'unique_alerts': unique_alerts,
            'alert_timeline': alert_timeline[-50:],  # Last 50 events
            'score_timeline': score_timeline[-50:],
            'risk_distribution': {
                'low': round(low_risk, 1),
                'medium': round(medium_risk, 1),
                'high': round(high_risk, 1)
            },
            'alert_frequency': round(alert_frequency, 2),
            'peak_risk_times': peak_times,
            'integrity_stats': integrity_stats,
            'summary': summary
        }
    
    def get_exam_analytics(self, exam_id):
        """Get aggregated analytics for all sessions of an exam"""
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Get all distinct session IDs for this exam
        cursor.execute("""
            SELECT DISTINCT session_id, student_id
            FROM events 
            WHERE session_id LIKE ?
        """, (f'%exam_{exam_id}%',))
        
        sessions = cursor.fetchall()
        conn.close()
        
        if not sessions:
            return None
        
        all_scores = []
        all_durations = []
        alert_counts = []
        
        for session_id, student_id in sessions:
            session_data = self.get_session_analytics(session_id)
            if session_data:
                all_scores.append(session_data['integrity_stats']['avg_score'])
                all_durations.append(session_data['duration'])
                alert_counts.append(session_data['summary']['total_alerts'])
        
        if not all_scores:
            return None
        
        # Calculate averages
        avg_score = sum(all_scores) / len(all_scores)
        avg_duration = sum(all_durations) / len(all_durations) if all_durations else 0
        total_alerts = sum(alert_counts)
        
        # Score distribution
        score_ranges = [
            {'range': '0-60', 'count': len([s for s in all_scores if s < 60])},
            {'range': '60-70', 'count': len([s for s in all_scores if 60 <= s < 70])},
            {'range': '70-80', 'count': len([s for s in all_scores if 70 <= s < 80])},
            {'range': '80-90', 'count': len([s for s in all_scores if 80 <= s < 90])},
            {'range': '90-100', 'count': len([s for s in all_scores if s >= 90])}
        ]
        
        # Performance groups
        performance_groups = {
            'excellent': len([s for s in all_scores if s >= 90]),
            'good': len([s for s in all_scores if 80 <= s < 90]),
            'fair': len([s for s in all_scores if 70 <= s < 80]),
            'poor': len([s for s in all_scores if s < 70])
        }
        
        return {
            'exam_id': exam_id,
            'total_sessions': len(sessions),
            'avg_integrity_score': round(avg_score, 1),
            'std_integrity_score': round(math.sqrt(sum((s - avg_score) ** 2 for s in all_scores) / len(all_scores)), 1),
            'avg_duration': round(avg_duration, 1),
            'total_alerts': total_alerts,
            'avg_alerts_per_session': round(total_alerts / len(sessions), 1) if sessions else 0,
            'score_distribution': score_ranges,
            'performance_groups': performance_groups
        }
    
    def generate_charts(self, analytics, type='session'):
        """Return chart data instead of generating images (to avoid matplotlib)"""
        charts = {}
        
        if type == 'session':
            # Return data for frontend to render charts
            if analytics.get('score_timeline'):
                charts['score_data'] = analytics['score_timeline']
            
            if analytics.get('unique_alerts'):
                charts['alert_data'] = analytics['unique_alerts'][:10]
            
            if analytics.get('risk_distribution'):
                charts['risk_data'] = analytics['risk_distribution']
        
        elif type == 'exam':
            if analytics.get('score_distribution'):
                charts['score_dist_data'] = analytics['score_distribution']
            
            if analytics.get('performance_groups'):
                charts['performance_data'] = analytics['performance_groups']
        
        return charts