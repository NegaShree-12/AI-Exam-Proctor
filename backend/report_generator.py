# backend/report_generator.py
import sqlite3
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from analytics_engine import AnalyticsEngine

DATABASE_FILE = 'proctoring_data.db'

def generate_report(student_id, session_id, output_filename):
    """Generate detailed violation report with timeline"""
    
    # Get analytics data
    analytics_engine = AnalyticsEngine()
    analytics = analytics_engine.get_session_analytics(session_id)
    
    if not analytics:
        print(f"No data found for student {student_id} and session {session_id}")
        return None
    
    # Create PDF
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle(name='CenterTitle', parent=styles['h1'], alignment=TA_CENTER))
    styles.add(ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=TA_RIGHT))
    styles.add(ParagraphStyle(name='ViolationText', parent=styles['Normal'], fontSize=9, textColor=colors.red))
    
    story = []
    
    # ===== COVER PAGE =====
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Proctoring Session", styles['CenterTitle']))
    story.append(Paragraph("Violation Report", styles['CenterTitle']))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Student: {student_id}", styles['CenterTitle']))
    story.append(Paragraph(f"Session: {session_id}", styles['CenterTitle']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['RightAlign']))
    story.append(PageBreak())
    
    # ===== EXECUTIVE SUMMARY =====
    story.append(Paragraph("Executive Summary", styles['h1']))
    story.append(Spacer(1, 0.2*inch))
    
    terminated = analytics.get('summary', {}).get('terminated', False)
    final_score = analytics['integrity_stats']['final_score']
    
    if terminated:
        decision = "❌ FAIL - Exam Automatically Terminated"
        decision_color = colors.red
    elif final_score >= 80:
        decision = "✅ PASS"
        decision_color = colors.green
    elif final_score >= 70:
        decision = "⚠️ PASS WITH CAUTION"
        decision_color = colors.orange
    else:
        decision = "❌ FAIL"
        decision_color = colors.red
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Final Decision', decision],
        ['Final Score', f"{final_score} / 100"],
        ['Session Duration', f"{analytics['duration']} minutes"],
        ['Total Violations', str(analytics['summary']['total_alerts'])],
        ['Serious Violations', str(analytics['summary'].get('serious_violations', 0))],
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 3.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -2), colors.whitesmoke),
        ('BACKGROUND', (0, -1), (-1, -1), decision_color),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.white if decision_color == colors.red else colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    story.append(Paragraph(f"<b>Recommendation:</b> {analytics['summary']['recommendation']}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # ===== VIOLATION DETAILS =====
    story.append(Paragraph("Violation Details", styles['h1']))
    story.append(Spacer(1, 0.2*inch))
    
    if analytics['alert_timeline']:
        timeline_data = [['Time', 'Violation', 'Score']]
        
        for item in analytics['alert_timeline']:
            time_str = item['time']
            alerts = item['alerts']
            score = item['score']
            
            if alerts:
                for alert in alerts:
                    alert_text = alert
                    if any(s in alert for s in ["PHONE", "Multiple faces", "BOOK", "LAPTOP"]):
                        alert_text = f"🔴 SERIOUS: {alert}"
                    elif "VOICE:" in alert:
                        alert_text = f"🗣️ {alert}"
                    
                    timeline_data.append([time_str, alert_text, str(score)])
                    time_str = ""  # Only show time for first alert in group
        
        # Limit to last 30 entries
        if len(timeline_data) > 31:
            timeline_data = timeline_data[:31]
            timeline_data.append(["", f"... and {len(timeline_data)-31} more violations", ""])
        
        timeline_table = Table(timeline_data, colWidths=[1*inch, 4*inch, 0.8*inch])
        timeline_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(timeline_table)
    else:
        story.append(Paragraph("No violations recorded.", styles['Normal']))
    
    # ===== VOICE TRANSCRIPTS =====
    voice_transcripts = []
    for item in analytics['alert_timeline']:
        for alert in item['alerts']:
            if "VOICE:" in alert:
                voice_transcripts.append({
                    'time': item['time'],
                    'text': alert.replace("VOICE:", "").strip()
                })
    
    if voice_transcripts:
        story.append(PageBreak())
        story.append(Paragraph("Voice Activity Transcript", styles['h1']))
        story.append(Spacer(1, 0.2*inch))
        
        transcript_data = [['Time', 'Spoken Text']]
        for vt in voice_transcripts[-10:]:  # Last 10 voice events
            transcript_data.append([vt['time'], vt['text']])
        
        transcript_table = Table(transcript_data, colWidths=[1.5*inch, 4*inch])
        transcript_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        story.append(transcript_table)
    
    # ===== RECOMMENDATIONS =====
    story.append(PageBreak())
    story.append(Paragraph("Recommendations", styles['h1']))
    story.append(Spacer(1, 0.2*inch))
    
    if terminated:
        story.append(Paragraph("❌ This exam was automatically terminated due to:", styles['ViolationText']))
        for v in analytics['summary'].get('violation_types', [])[:3]:
            story.append(Paragraph(f"   • {v}", styles['ViolationText']))
        story.append(Spacer(1, 0.1*inch))
        story.append(Paragraph("Action Required: Schedule a disciplinary meeting with the student.", styles['Normal']))
    elif final_score >= 90:
        story.append(Paragraph("✓ Student maintained excellent integrity throughout the exam.", styles['Normal']))
    elif final_score >= 80:
        story.append(Paragraph("⚠️ Student had minor violations. Review the violation log above.", styles['Normal']))
    else:
        story.append(Paragraph("❌ Serious integrity violations detected. Consider invalidating this attempt.", styles['Normal']))
    
    # Generate PDF
    try:
        doc.build(story)
        return output_filename
    except Exception as e:
        print(f"Error building PDF: {e}")
        return None