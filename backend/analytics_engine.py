import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

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
        
        # Load session data
        query = "SELECT * FROM events WHERE session_id = ? ORDER BY timestamp ASC"
        df = pd.read_sql_query(query, conn, params=(session_id,))
        conn.close()
        
        if df.empty:
            return None
        
        # Parse JSON fields
        df['alerts'] = df['alerts'].apply(lambda x: json.loads(x) if x else [])
        df['metrics'] = df['metrics'].apply(lambda x: json.loads(x) if x else {})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Calculate analytics
        analytics = {
            'session_id': session_id,
            'student_id': df['student_id'].iloc[0],
            'duration': self._calculate_duration(df),
            'total_events': len(df),
            'unique_alerts': self._get_unique_alerts(df),
            'alert_timeline': self._create_alert_timeline(df),
            'score_timeline': self._create_score_timeline(df),
            'risk_distribution': self._calculate_risk_distribution(df),
            'alert_frequency': self._calculate_alert_frequency(df),
            'peak_risk_times': self._find_peak_risk_times(df),
            'emotion_data': self._extract_emotion_data(df),
            'integrity_stats': self._calculate_integrity_stats(df),
            'summary': self._generate_summary(df)
        }
        
        return analytics
    
    def get_exam_analytics(self, exam_id):
        """Get aggregated analytics for all sessions of an exam"""
        conn = sqlite3.connect(DATABASE_FILE)
        
        # Get all sessions for this exam
        query = """
            SELECT DISTINCT session_id, student_id 
            FROM events 
            WHERE session_id LIKE ?
        """
        df_sessions = pd.read_sql_query(query, conn, params=(f'%exam_{exam_id}%',))
        conn.close()
        
        if df_sessions.empty:
            return None
        
        # Collect analytics for each session
        all_scores = []
        all_durations = []
        alert_counts = []
        
        for _, row in df_sessions.iterrows():
            session_data = self.get_session_analytics(row['session_id'])
            if session_data:
                all_scores.append(session_data['integrity_stats']['avg_score'])
                all_durations.append(session_data['duration'])
                alert_counts.append(len(session_data['unique_alerts']))
        
        # Calculate exam-wide statistics
        exam_analytics = {
            'exam_id': exam_id,
            'total_sessions': len(df_sessions),
            'avg_integrity_score': np.mean(all_scores) if all_scores else 0,
            'std_integrity_score': np.std(all_scores) if all_scores else 0,
            'avg_duration': np.mean(all_durations) if all_durations else 0,
            'total_alerts': sum(alert_counts),
            'avg_alerts_per_session': np.mean(alert_counts) if alert_counts else 0,
            'score_distribution': self._create_score_distribution(all_scores),
            'performance_groups': self._group_performance(all_scores)
        }
        
        return exam_analytics
    
    def generate_charts(self, analytics, type='session'):
        """Generate base64 encoded charts for reports"""
        charts = {}
        
        if type == 'session':
            # Alert timeline chart
            charts['alert_timeline'] = self._create_alert_timeline_chart(analytics)
            
            # Score progression chart
            charts['score_progression'] = self._create_score_chart(analytics)
            
            # Alert pie chart
            charts['alert_pie'] = self._create_alert_pie_chart(analytics)
            
            # Risk heatmap
            charts['risk_heatmap'] = self._create_risk_heatmap(analytics)
        
        elif type == 'exam':
            # Score distribution histogram
            charts['score_dist'] = self._create_score_distribution_chart(analytics)
            
            # Performance comparison
            charts['performance_comp'] = self._create_performance_chart(analytics)
        
        return charts
    
    def _calculate_duration(self, df):
        """Calculate session duration in minutes"""
        if len(df) < 2:
            return 0
        duration = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds() / 60
        return round(duration, 2)
    
    def _get_unique_alerts(self, df):
        """Get unique alerts with counts"""
        all_alerts = []
        for alerts in df['alerts']:
            all_alerts.extend(alerts)
        
        alert_counts = Counter(all_alerts)
        return [{'alert': alert, 'count': count} for alert, count in alert_counts.most_common()]
    
    def _create_alert_timeline(self, df):
        """Create timeline of alerts over time"""
        timeline = []
        for _, row in df.iterrows():
            if row['alerts']:
                timeline.append({
                    'time': row['timestamp'].strftime('%H:%M:%S'),
                    'alerts': row['alerts'],
                    'score': row['integrity_score']
                })
        return timeline
    
    def _create_score_timeline(self, df):
        """Create timeline of integrity scores"""
        return [
            {
                'time': row['timestamp'].strftime('%H:%M:%S'),
                'score': row['integrity_score']
            }
            for _, row in df.iterrows()
        ]
    
    def _calculate_risk_distribution(self, df):
        """Calculate percentage of time in each risk level"""
        total_time = len(df)
        if total_time == 0:
            return {'low': 0, 'medium': 0, 'high': 0}
        
        scores = df['integrity_score']
        low_risk = len(scores[scores >= 80]) / total_time * 100
        medium_risk = len(scores[(scores >= 60) & (scores < 80)]) / total_time * 100
        high_risk = len(scores[scores < 60]) / total_time * 100
        
        return {
            'low': round(low_risk, 1),
            'medium': round(medium_risk, 1),
            'high': round(high_risk, 1)
        }
    
    def _calculate_alert_frequency(self, df):
        """Calculate alerts per minute"""
        duration_min = self._calculate_duration(df)
        if duration_min == 0:
            return 0
        
        total_alerts = sum(len(alerts) for alerts in df['alerts'])
        return round(total_alerts / duration_min, 2)
    
    def _find_peak_risk_times(self, df):
        """Find times with highest risk"""
        if len(df) < 5:
            return []
        
        # Group into 5-minute intervals
        df['time_group'] = df['timestamp'].dt.floor('5min')
        grouped = df.groupby('time_group')['integrity_score'].mean()
        
        # Find lowest scoring intervals
        peak_times = grouped.nsmallest(3)
        
        return [
            {
                'time': time.strftime('%H:%M'),
                'avg_score': round(score, 1)
            }
            for time, score in peak_times.items()
        ]
    
    def _extract_emotion_data(self, df):
        """Extract emotion data from metrics"""
        emotions = []
        for metrics in df['metrics']:
            if isinstance(metrics, dict) and 'emotion' in metrics:
                emotions.append(metrics['emotion'])
        
        if not emotions:
            return {}
        
        emotion_counts = Counter(emotions)
        total = len(emotions)
        
        return {
            emotion: round(count / total * 100, 1)
            for emotion, count in emotion_counts.items()
        }
    
    def _calculate_integrity_stats(self, df):
        """Calculate integrity score statistics with higher penalties"""
        scores = df['integrity_score']
        
        # Check if exam was terminated
        terminated = any("EXAM_TERMINATED" in str(alerts) for alerts in df['alerts'])
        
        if terminated:
            final_score = 0  # Auto-fail terminated exams
        else:
            final_score = round(scores.iloc[-1], 1) if not scores.empty else 0
        
        return {
            'avg_score': round(scores.mean(), 1),
            'min_score': round(scores.min(), 1),
            'max_score': round(scores.max(), 1),
            'std_score': round(scores.std(), 1),
            'final_score': final_score,
            'terminated': terminated
        }
    
    def _generate_summary(self, df):
        """Generate natural language summary with violation details"""
        stats = self._calculate_integrity_stats(df)
        risk_dist = self._calculate_risk_distribution(df)
        
        # Check for serious violations
        all_alerts = []
        for alerts in df['alerts']:
            all_alerts.extend(alerts)
        
        serious_violations = [a for a in all_alerts if any(
            s in a for s in ["PHONE", "Multiple faces", "BOOK", "LAPTOP", "EXAM_TERMINATED"]
        )]
        
        if stats.get('terminated', False):
            integrity_level = "FAILED - Exam Terminated"
            recommendation = "Exam was automatically terminated due to serious violation"
        elif stats['avg_score'] >= 90:
            integrity_level = "Excellent"
            recommendation = "No action needed"
        elif stats['avg_score'] >= 80:
            integrity_level = "Good"
            recommendation = "Minor review recommended"
        elif stats['avg_score'] >= 70:
            integrity_level = "Fair"
            recommendation = "Manual review required"
        else:
            integrity_level = "Poor"
            recommendation = "Serious concerns - investigate thoroughly"
        
        return {
            'integrity_level': integrity_level,
            'recommendation': recommendation,
            'total_alerts': len(all_alerts),
            'serious_violations': len(serious_violations),
            'violation_types': list(set(serious_violations)),
            'risk_level': 'HIGH' if risk_dist['high'] > 30 or len(serious_violations) > 5 else 'MEDIUM' if risk_dist['high'] > 10 else 'LOW',
            'terminated': stats.get('terminated', False)
        }
    
    def _create_score_distribution(self, scores):
        """Create score distribution data"""
        if not scores:
            return []
        
        bins = [0, 60, 70, 80, 90, 100]
        labels = ['0-60', '60-70', '70-80', '80-90', '90-100']
        
        hist, _ = np.histogram(scores, bins=bins)
        
        return [
            {'range': labels[i], 'count': int(hist[i])}
            for i in range(len(labels))
        ]
    
    def _group_performance(self, scores):
        """Group students by performance"""
        if not scores:
            return {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
        
        return {
            'excellent': len([s for s in scores if s >= 90]),
            'good': len([s for s in scores if 80 <= s < 90]),
            'fair': len([s for s in scores if 70 <= s < 80]),
            'poor': len([s for s in scores if s < 70])
        }
    
    def _create_alert_timeline_chart(self, analytics):
        """Create matplotlib chart of alerts over time"""
        plt.figure(figsize=(10, 4))
        
        timeline = analytics['alert_timeline']
        if not timeline:
            return None
        
        times = [t['time'] for t in timeline]
        alert_counts = [len(t['alerts']) for t in timeline]
        
        plt.plot(times, alert_counts, marker='o', linestyle='-', color='red', linewidth=2)
        plt.title('Alert Frequency Timeline')
        plt.xlabel('Time')
        plt.ylabel('Number of Alerts')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convert to base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64
    
    def _create_score_chart(self, analytics):
        """Create score progression chart"""
        plt.figure(figsize=(10, 4))
        
        timeline = analytics['score_timeline']
        if not timeline:
            return None
        
        times = [t['time'] for t in timeline]
        scores = [t['score'] for t in timeline]
        
        plt.plot(times, scores, marker='s', linestyle='-', color='blue', linewidth=2)
        plt.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='Good')
        plt.axhline(y=60, color='orange', linestyle='--', alpha=0.5, label='Warning')
        plt.axhline(y=40, color='red', linestyle='--', alpha=0.5, label='Critical')
        plt.title('Integrity Score Progression')
        plt.xlabel('Time')
        plt.ylabel('Score')
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64
    
    def _create_alert_pie_chart(self, analytics):
        """Create pie chart of alert types"""
        unique_alerts = analytics['unique_alerts']
        if not unique_alerts:
            return None
        
        alerts = [u['alert'][:20] + '...' if len(u['alert']) > 20 else u['alert'] for u in unique_alerts[:5]]
        counts = [u['count'] for u in unique_alerts[:5]]
        
        plt.figure(figsize=(8, 8))
        plt.pie(counts, labels=alerts, autopct='%1.1f%%', startangle=90)
        plt.title('Alert Distribution')
        plt.axis('equal')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64
    
    def _create_risk_heatmap(self, analytics):
        """Create risk heatmap over time"""
        timeline = analytics['alert_timeline']
        if not timeline:
            return None
        
        # Create 10x10 heatmap of risk levels
        risk_matrix = np.random.rand(10, 10) * 100  # Placeholder - replace with actual logic
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(risk_matrix, annot=True, fmt='.1f', cmap='YlOrRd')
        plt.title('Risk Heat Map')
        plt.xlabel('Time Interval')
        plt.ylabel('Risk Level')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64
    
    def _create_score_distribution_chart(self, analytics):
        """Create histogram of score distribution"""
        if 'score_distribution' not in analytics:
            return None
        
        dist = analytics['score_distribution']
        ranges = [d['range'] for d in dist]
        counts = [d['count'] for d in dist]
        
        plt.figure(figsize=(8, 5))
        bars = plt.bar(ranges, counts, color=['red', 'orange', 'yellow', 'lightgreen', 'green'])
        plt.title('Score Distribution Across Students')
        plt.xlabel('Score Range')
        plt.ylabel('Number of Students')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64
    
    def _create_performance_chart(self, analytics):
        """Create performance comparison chart"""
        groups = analytics.get('performance_groups', {})
        
        categories = list(groups.keys())
        values = list(groups.values())
        
        plt.figure(figsize=(8, 5))
        colors = ['green', 'lightgreen', 'orange', 'red']
        bars = plt.bar(categories, values, color=colors)
        plt.title('Student Performance Groups')
        plt.xlabel('Performance Level')
        plt.ylabel('Number of Students')
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        
        return img_base64