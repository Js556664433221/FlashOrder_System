import psycopg2
import hashlib

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/flashorder')
cur = conn.cursor()

# Update admin password with correct hash
admin_hash = hash_password("admin123")
cur.execute("UPDATE users SET hashed_password = %s WHERE username = 'admin'", (admin_hash,))
conn.commit()
print(f"Admin password updated. Hash: {admin_hash}")

# Update staff password with correct hash
staff_hash = hash_password("staff123")
cur.execute("UPDATE users SET hashed_password = %s WHERE username = 'staff'", (staff_hash,))
conn.commit()
print(f"Staff password updated. Hash: {staff_hash}")

conn.close()