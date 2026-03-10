# check_db.py
import sqlite3
import json

conn = sqlite3.connect('proctoring_data.db')
cursor = conn.cursor()

print("="*50)
print("📊 DATABASE DEBUG")
print("="*50)

# 1. Check all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"\n📋 Tables: {[t[0] for t in tables]}")

# 2. Check users
cursor.execute("SELECT id, username, role FROM users")
users = cursor.fetchall()
print(f"\n👥 Users: {users}")

# 3. Check exams
cursor.execute("SELECT id, title FROM exams")
exams = cursor.fetchall()
print(f"\n📝 Exams: {exams}")

# 4. Check exam_assignments
cursor.execute("SELECT * FROM exam_assignments")
assignments = cursor.fetchall()
print(f"\n📎 Assignments: {assignments}")

# 5. Check ALL events (most important!)
cursor.execute("SELECT student_id, session_id, COUNT(*) FROM events GROUP BY session_id")
events = cursor.fetchall()
print(f"\n🎯 ALL SESSIONS IN DATABASE:")
for event in events:
    print(f"   Student: {event[0]}, Session: {event[1]}, Count: {event[2]}")

# 6. Check specifically for exam 1
cursor.execute("SELECT * FROM events WHERE session_id LIKE '%exam_1%' LIMIT 5")
exam_events = cursor.fetchall()
print(f"\n🔍 Events for exam 1: {len(exam_events)}")
for event in exam_events:
    print(f"   {event}")

# 7. Check what the API query would return
exam_id = 1
cursor.execute("""
    SELECT u.username 
    FROM exam_assignments a
    JOIN users u ON a.student_id = u.id
    WHERE a.exam_id = ?
""", (exam_id,))
students = cursor.fetchall()
print(f"\n👤 Students assigned to exam {exam_id}: {[s[0] for s in students]}")

if students:
    student_usernames = [s[0] for s in students]
    placeholders = ','.join('?' for _ in student_usernames)
    
    # Test the query
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
    """
    params = student_usernames + [f'%exam_{exam_id}%']
    cursor.execute(query, params)
    results = cursor.fetchall()
    print(f"\n📊 Query results: {results}")

conn.close()