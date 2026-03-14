import sqlite3
from werkzeug.security import generate_password_hash

# Connect to database
conn = sqlite3.connect('proctoring_data.db')
cursor = conn.cursor()

# Reset NEGA's password
username = "NEGA"
new_password = "bitsathyl16"  # You can change this

# Generate password hash
password_hash = generate_password_hash(new_password)

# Update the password
cursor.execute("""
    UPDATE users 
    SET password_hash = ? 
    WHERE username = ?
""", (password_hash, username))

if cursor.rowcount > 0:
    print(f"✅ Password reset successful for {username}")
    print(f"   New password: {new_password}")
else:
    print(f"❌ User {username} not found!")

conn.commit()
conn.close()