import sqlite3
import json

print("="*60)
print("🔍 PROCTORAI+ DATABASE DEBUGGER")
print("="*60)

# Connect to database
conn = sqlite3.connect('proctoring_data.db')
cursor = conn.cursor()

# 1. List all tables
print("\n📋 TABLES IN DATABASE:")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"   - {table[0]}")

# 2. Check USERS table
print("\n👥 USERS TABLE:")
try:
    cursor.execute("SELECT id, username, role FROM users")
    users = cursor.fetchall()
    print(f"   Found {len(users)} users:")
    for user in users:
        print(f"   ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")
except Exception as e:
    print(f"   Error: {e}")

# 3. Check EXAMS table
print("\n📝 EXAMS TABLE:")
try:
    cursor.execute("SELECT id, title, description FROM exams")
    exams = cursor.fetchall()
    print(f"   Found {len(exams)} exams:")
    for exam in exams:
        print(f"   ID: {exam[0]}, Title: {exam[1]}, Desc: {exam[2]}")
except Exception as e:
    print(f"   Error: {e}")

# 4. Check EXAM_ASSIGNMENTS table
print("\n🔗 EXAM ASSIGNMENTS TABLE:")
try:
    cursor.execute("SELECT * FROM exam_assignments")
    assignments = cursor.fetchall()
    print(f"   Found {len(assignments)} assignments:")
    for a in assignments:
        print(f"   {a}")
except Exception as e:
    print(f"   Error: {e}")

# 5. Check EVENTS table - summary
print("\n🎯 EVENTS TABLE SUMMARY:")
try:
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    print(f"   Total events: {total_events}")
    
    cursor.execute("SELECT DISTINCT student_id FROM events")
    students = cursor.fetchall()
    print(f"   Students with events: {[s[0] for s in students]}")
    
    cursor.execute("""
        SELECT student_id, COUNT(*) as count 
        FROM events 
        GROUP BY student_id
    """)
    counts = cursor.fetchall()
    for student_id, count in counts:
        print(f"   - {student_id}: {count} events")
        
    # Show sample events
    print("\n   Sample events (first 3):")
    cursor.execute("SELECT id, student_id, session_id, timestamp, alerts FROM events LIMIT 3")
    samples = cursor.fetchall()
    for sample in samples:
        print(f"   ID: {sample[0]}, Student: {sample[1]}")
        print(f"      Session: {sample[2]}")
        print(f"      Time: {sample[3]}")
        print(f"      Alerts: {sample[4][:50]}...")
        
except Exception as e:
    print(f"   Error: {e}")

# 6. Check specifically for exam 1 sessions
print("\n🔎 EXAM 1 SESSIONS:")
try:
    cursor.execute("""
        SELECT student_id, session_id, COUNT(*) 
        FROM events 
        WHERE session_id LIKE '%exam_1%'
        GROUP BY session_id
        ORDER BY student_id
    """)
    sessions = cursor.fetchall()
    print(f"   Found {len(sessions)} sessions for exam 1:")
    for student_id, session_id, count in sessions:
        print(f"   - {student_id}: {session_id}")
        print(f"     Events: {count}")
        
        # Check if this student is assigned to exam 1
        cursor.execute("""
            SELECT * FROM exam_assignments 
            WHERE exam_id = 1 AND student_id = (
                SELECT id FROM users WHERE username = ?
            )
        """, (student_id,))
        assigned = cursor.fetchone()
        if assigned:
            print(f"     ✅ Student is ASSIGNED to exam 1")
        else:
            print(f"     ❌ Student is NOT assigned to exam 1")
            
except Exception as e:
    print(f"   Error: {e}")

# 7. Check the JOIN query that the API uses
print("\n🔄 TESTING API QUERY:")
try:
    exam_id = 1
    # Get students assigned to this exam
    cursor.execute("""
        SELECT u.username 
        FROM exam_assignments a
        JOIN users u ON a.student_id = u.id
        WHERE a.exam_id = ?
    """, (exam_id,))
    students = cursor.fetchall()
    print(f"   Students assigned to exam {exam_id}: {[s[0] for s in students]}")
    
    if students:
        student_usernames = [s[0] for s in students]
        placeholders = ','.join('?' for _ in student_usernames)
        
        # This is the actual API query
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
        
        print(f"\n   Executing query with params: {params}")
        cursor.execute(query, params)
        results = cursor.fetchall()
        print(f"   Query returned {len(results)} results:")
        for r in results:
            print(f"   - {r}")
    else:
        print("   ❌ No students assigned to this exam!")
        
except Exception as e:
    print(f"   Error in query: {e}")

conn.close()

print("\n" + "="*60)
print("✅ DEBUG COMPLETE")
print("="*60)