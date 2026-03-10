import sqlite3
from werkzeug.security import generate_password_hash

# Connect to database
conn = sqlite3.connect('proctoring_data.db')
cursor = conn.cursor()

# Show current users
print("👥 Current users:")
cursor.execute("SELECT id, username, role FROM users")
for user in cursor.fetchall():
    print(f"   ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")

# Reset vishwas password to 'admin123'
new_password = generate_password_hash('admin123')
cursor.execute("""
    UPDATE users 
    SET password_hash = ? 
    WHERE username = 'vishwas'
""", (new_password,))

conn.commit()

# Verify it worked
cursor.execute("SELECT username, role FROM users WHERE username = 'vishwas'")
result = cursor.fetchone()
if result:
    print(f"\n✅ Password reset successful for: {result[0]} ({result[1]})")
    print(f"   New password: admin123")
else:
    print("\n❌ User 'vishwas' not found!")

conn.close()