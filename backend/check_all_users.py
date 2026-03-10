import sqlite3

conn = sqlite3.connect('proctoring_data.db')
cursor = conn.cursor()

print("🔍 ALL USERS IN DATABASE")
print("="*50)

cursor.execute("SELECT id, username, role FROM users")
users = cursor.fetchall()

for user in users:
    print(f"ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")

conn.close()