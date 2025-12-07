import sqlite3
import os

# Try common DB locations relative to project root
candidates = [os.path.join('instance','zit_online.db'), 'zit_online.db']

for p in candidates:
    if os.path.exists(p):
        print('Using DB:', p)
        try:
            conn = sqlite3.connect(p)
            cur = conn.cursor()
            cur.execute("SELECT email, role FROM user WHERE email = ?", ('admin@zit.edu',))
            row = cur.fetchone()
            if row:
                print('FOUND', row[0], row[1])
            else:
                print('NOTFOUND')
        except Exception as e:
            print('ERROR:', e)
        finally:
            try:
                conn.close()
            except:
                pass
        break
else:
    print('NO_DB_FILE_FOUND')
