import sqlite3
conn = sqlite3.connect('zit_online.db')
cur = conn.cursor()
cur.execute("PRAGMA table_info('course');")
rows = cur.fetchall()
for r in rows:
    print(r)
conn.close()
