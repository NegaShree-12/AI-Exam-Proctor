import sqlite3
import requests
import json

print("="*60)
print("🏆 FINAL FIX - EXAM ASSIGNMENTS")
print("="*60)

# Connect to database
conn = sqlite3.connect('proctoring_data.db')
cursor = conn.cursor()

# 1. Show all tables
print("\n📊 DATABASE STATUS")
print("-"*40)

# Users
cursor.execute("SELECT id, username, role FROM users")
users = cursor.fetchall()
print(f"\n👥 Users ({len(users)}):")
for user in users:
    print(f"   ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")

# Exams
cursor.execute("SELECT id, title FROM exams")
exams = cursor.fetchall()
print(f"\n📝 Exams ({len(exams)}):")
for exam in exams:
    print(f"   ID: {exam[0]}, Title: {exam[1]}")

# 2. Make sure exam 1 exists
cursor.execute("SELECT id FROM exams WHERE id = 1")
if not cursor.fetchone():
    print("\n📝 Creating exam 1...")
    cursor.execute("""
        INSERT INTO exams (id, title, description, created_by_admin_id)
        VALUES (1, 'sample', 'Sample exam for testing', 1)
    """)
    print("✅ Exam 1 created")

# 3. Get admin ID (or create admin)
cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
admin = cursor.fetchone()
if not admin:
    print("\n👑 Creating admin user...")
    from werkzeug.security import generate_password_hash
    cursor.execute("""
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, 'admin')
    """, ('admin', generate_password_hash('admin123')))
    admin_id = cursor.lastrowid
    print(f"✅ Admin created with ID: {admin_id}")
else:
    admin_id = admin[0]
    print(f"\n👑 Admin ID: {admin_id}")

# 4. Get all students
cursor.execute("SELECT id, username FROM users WHERE role = 'student'")
students = cursor.fetchall()

if not students:
    print("\n👤 Creating test students...")
    from werkzeug.security import generate_password_hash
    # Create student1
    cursor.execute("""
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, 'student')
    """, ('student1', generate_password_hash('student123')))
    
    # Create NEGA if you want
    cursor.execute("""
        INSERT OR IGNORE INTO users (username, password_hash, role)
        VALUES (?, ?, 'student')
    """, ('NEGA', generate_password_hash('nega123')))
    
    # Get all students again
    cursor.execute("SELECT id, username FROM users WHERE role = 'student'")
    students = cursor.fetchall()
    print(f"✅ Created {len(students)} students")

# 5. Assign ALL students to exam 1
print("\n🔗 Assigning students to exam 1...")
for student_id, username in students:
    # Check if already assigned
    cursor.execute("""
        SELECT * FROM exam_assignments 
        WHERE exam_id = 1 AND student_id = ?
    """, (student_id,))
    
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO exam_assignments (exam_id, student_id, status, assigned_at)
            VALUES (1, ?, 'assigned', datetime('now'))
        """, (student_id,))
        print(f"   ✅ Assigned {username} (ID: {student_id}) to exam 1")
    else:
        print(f"   ✅ {username} already assigned to exam 1")

conn.commit()

# 6. Verify assignments
print("\n📋 VERIFYING ASSIGNMENTS:")
cursor.execute("""
    SELECT e.title, u.username, a.status, a.assigned_at
    FROM exam_assignments a
    JOIN exams e ON a.exam_id = e.id
    JOIN users u ON a.student_id = u.id
    WHERE a.exam_id = 1
    ORDER BY u.username
""")
assignments = cursor.fetchall()
if assignments:
    for title, username, status, assigned_at in assignments:
        print(f"   📌 Exam: {title} -> Student: {username} ({status}) - {assigned_at}")
else:
    print("   ❌ No assignments found!")

# 7. Check events for exam 1
print("\n🎯 EVENTS FOR EXAM 1:")
cursor.execute("""
    SELECT student_id, COUNT(*) as event_count, 
           MIN(timestamp) as first_event, 
           MAX(timestamp) as last_event
    FROM events 
    WHERE session_id LIKE '%exam_1%'
    GROUP BY student_id
    ORDER BY student_id
""")
events = cursor.fetchall()
if events:
    for student_id, count, first, last in events:
        print(f"   📊 Student: {student_id}")
        print(f"      Events: {count}")
        print(f"      First: {first}")
        print(f"      Last: {last}")
        print(f"      ---")
else:
    print("   ❌ No events found for exam 1!")

# 8. Test the API endpoint directly
print("\n🌐 TESTING API ENDPOINT:")
try:
    response = requests.get("http://127.0.0.1:5000/api/exam_sessions/1")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Sessions found: {len(data)}")
        for session in data:
            print(f"   📁 {session}")
    else:
        print(f"   Error: {response.text}")
except Exception as e:
    print(f"   Connection error: {e}")

conn.close()

print("\n" + "="*60)
print("✅ FIX COMPLETE!")
print("="*60)
print("\n📌 NEXT STEPS:")
print("1. If you see 'No assignments found' above, run this script again")
print("2. If assignments exist but API shows none, restart Flask")
print("3. Refresh your admin page and click on 'sample' exam")