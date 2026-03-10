import sqlite3

print("🔧 FIXING EXAM ASSIGNMENTS")
print("="*40)

# Connect to database
conn = sqlite3.connect('proctoring_data.db')
cursor = conn.cursor()

# 1. Show all users
print("\n👥 Users in database:")
cursor.execute("SELECT id, username, role FROM users")
users = cursor.fetchall()
for user in users:
    print(f"   ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")

# 2. Show all exams
print("\n📝 Exams in database:")
cursor.execute("SELECT id, title FROM exams")
exams = cursor.fetchall()
for exam in exams:
    print(f"   ID: {exam[0]}, Title: {exam[1]}")

# 3. Create exam 1 if it doesn't exist
cursor.execute("SELECT id FROM exams WHERE id = 1")
if not cursor.fetchone():
    print("\n📝 Creating exam 1...")
    cursor.execute("""
        INSERT INTO exams (id, title, description, created_by_admin_id)
        VALUES (1, 'sample', 'Sample exam', 1)
    """)
    print("✅ Exam 1 created")

# 4. Assign ALL students to exam 1
print("\n🔗 Assigning students to exam 1...")

# Get all student IDs
cursor.execute("SELECT id, username FROM users WHERE role = 'student'")
students = cursor.fetchall()

for student_id, username in students:
    # Check if already assigned
    cursor.execute("""
        SELECT * FROM exam_assignments 
        WHERE exam_id = 1 AND student_id = ?
    """, (student_id,))
    
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO exam_assignments (exam_id, student_id, status)
            VALUES (1, ?, 'assigned')
        """, (student_id,))
        print(f"   ✅ Assigned {username} (ID: {student_id}) to exam 1")
    else:
        print(f"   ⏭️ {username} already assigned to exam 1")

conn.commit()

# 5. Verify assignments
print("\n📋 Current exam assignments:")
cursor.execute("""
    SELECT e.title, u.username, a.status
    FROM exam_assignments a
    JOIN exams e ON a.exam_id = e.id
    JOIN users u ON a.student_id = u.id
    WHERE a.exam_id = 1
""")
assignments = cursor.fetchall()
for exam_title, username, status in assignments:
    print(f"   Exam: {exam_title} -> Student: {username} ({status})")

# 6. Check events for NEGA
print("\n🎯 Events for NEGA:")
cursor.execute("""
    SELECT session_id, COUNT(*) 
    FROM events 
    WHERE student_id = 'NEGA' AND session_id LIKE '%exam_1%'
    GROUP BY session_id
""")
events = cursor.fetchall()
for session_id, count in events:
    print(f"   Session: {session_id} ({count} events)")

conn.close()

print("\n" + "="*40)
print("✅ FIX COMPLETE!")
print("="*40)
print("\n📌 NEXT STEPS:")
print("1. Restart your Flask backend (Ctrl+C then 'python app.py')")
print("2. Refresh your admin page")
print("3. Click on 'sample' exam again")