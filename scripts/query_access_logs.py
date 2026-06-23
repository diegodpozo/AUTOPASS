import sqlite3, os

db='parking.db'
if not os.path.exists(db):
    print('DB not found')
else:
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    plate='FG 112 LO'
    cur.execute("SELECT id,patente_detectada,tipo_evento,fecha_hora,pago_confirmado,sucursal FROM access_logs WHERE UPPER(REPLACE(patente_detectada,' ',''))=UPPER(REPLACE(?,' ','')) ORDER BY id DESC LIMIT 50", (plate,))
    rows=cur.fetchall()
    if not rows:
        print('No access logs for', plate)
    else:
        for r in rows:
            print(r)
    conn.close()
