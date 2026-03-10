# quick_check_live.py
import sqlite3

conn = sqlite3.connect('proctoring_data.db')
cursor = conn.cursor()

print("🔍 MANUAL DATABASE CHECK")
print("="*40)

# Check exam_assignments table structure
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='exam_assignments'")
print("\n📋 Table structure:")
print(cursor.fetchone()[0])

# Check all assignments
cursor.execute("SELECT * FROM exam_assignments")
assignments = cursor.fetchall()
print(f"\n📋 All assignments ({len(assignments)}):")
for a in assignments:
    print(f"   {a}")

# Check events grouped by session
cursor.execute("""
    SELECT student_id, session_id, COUNT(*) 
    FROM events 
    GROUP BY session_id
    ORDER BY student_id
""")
print("\n🎯 Events by session:")
for row in cursor.fetchall():
    print(f"   {row[0]}: {row[1]} - {row[2]} events")

conn.close()