import sqlite3, os, re

DB = 'parking.db'
if not os.path.exists(DB):
    print('parking.db not found')
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()
# Check if column exists
cur.execute("PRAGMA table_info('access_logs')")
cols = [r[1] for r in cur.fetchall()]
if 'normalized_patente' in cols:
    print('normalized_patente column already exists')
else:
    print('Adding normalized_patente column')
    cur.execute("ALTER TABLE access_logs ADD COLUMN normalized_patente TEXT")
    conn.commit()

# Backfill
cur.execute("SELECT id, patente_detectada FROM access_logs")
rows = cur.fetchall()
updated = 0
for r in rows:
    pid = r[0]
    p = r[1] or ''
    norm = re.sub(r'[^A-Z0-9]', '', p.upper())
    cur.execute('SELECT normalized_patente FROM access_logs WHERE id=?', (pid,))
    existing = cur.fetchone()[0]
    if existing != norm:
        cur.execute('UPDATE access_logs SET normalized_patente=? WHERE id=?', (norm, pid))
        updated += 1
        print('Backfilled', pid, p, '->', norm)

conn.commit()
# Create index
try:
    cur.execute('CREATE INDEX IF NOT EXISTS idx_access_logs_normalized_patente ON access_logs(normalized_patente)')
    conn.commit()
    print('Index created (or already existed)')
except Exception as e:
    print('Could not create index:', e)

print('Total backfilled:', updated)
conn.close()
