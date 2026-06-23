import sqlite3, os

db='parking.db'
if not os.path.exists(db):
    print('DB not found')
else:
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    target='FG 112 LO'
    norm=''.join(target.upper().split())
    cur.execute("SELECT id,patente_detectada FROM access_logs")
    rows=cur.fetchall()
    updated=0
    for r in rows:
        pid=r[0]; p=r[1]
        if p and ''.join(p.upper().split())==norm:
            newp=norm
            cur.execute('UPDATE access_logs SET patente_detectada=? WHERE id=?',(newp,pid))
            updated+=1
            print('Updated', pid, p, '->', newp)
    conn.commit()
    print('Total updated', updated)
    conn.close()
