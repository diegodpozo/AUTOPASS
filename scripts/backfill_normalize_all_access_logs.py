import sqlite3, os, re, datetime

DB = 'parking.db'
if not os.path.exists(DB):
    print('parking.db not found in current folder')
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT id, patente_detectada FROM access_logs")
rows = cur.fetchall()

updated = 0
for r in rows:
    pid = r[0]
    p = r[1]
    if not p:
        continue
    norm = re.sub(r'[^A-Z0-9]', '', p.upper())
    if norm != p:
        cur.execute('UPDATE access_logs SET patente_detectada=? WHERE id=?', (norm, pid))
        updated += 1
        print('Updated', pid, p, '->', norm)

conn.commit()
print('Total updated:', updated)
conn.close()
