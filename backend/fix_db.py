import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/flashorder')
cur = conn.cursor()

# Check if user_id column exists
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='orders' AND column_name='user_id'")
if not cur.fetchone():
    # Add user_id column
    cur.execute('ALTER TABLE orders ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1')
    conn.commit()
    # Set all existing orders to user_id=1 (admin)
    cur.execute('UPDATE orders SET user_id = 1 WHERE user_id IS NULL')
    conn.commit()
    print('user_id column added to orders')
else:
    print('user_id column already exists')

conn.close()