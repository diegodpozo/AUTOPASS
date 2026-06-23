import sqlite3, os

db='parking.db'
if not os.path.exists(db):
    print('DB not found')
else:
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    cur.execute('SELECT id,email,nombre,apellido,sucursal,rol FROM users')
    rows=cur.fetchall()
    for r in rows:
        print(r)
    conn.close()
