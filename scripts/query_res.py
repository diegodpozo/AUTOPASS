import sqlite3, os

db='parking.db'
if not os.path.exists(db):
    print('DB not found', db)
else:
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    try:
        cur.execute('SELECT id,patente,sucursal_nombre,fecha_inicio,fecha_fin,estado_pago FROM reservations')
        rows=cur.fetchall()
        found=[r for r in rows if r[1] and 'FG' in r[1].upper()]
        if not found:
            print('No reservations found for plate FG')
        else:
            for r in found:
                print('RES:', r)
    except Exception as e:
        print('ERROR', e)
    conn.close()
