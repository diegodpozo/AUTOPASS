import sqlite3, re
DB='parking.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
pat='FG 112 LO'
norm=re.sub(r'[^A-Z0-9]','',pat.upper())
print('Normalized:', norm)
print('\nReservations for plate:')
cur.execute('''SELECT id, patente, estado_pago, estado_reserva, fecha_inicio, fecha_fin, sucursal_nombre, monto_total FROM reservations WHERE UPPER(patente) LIKE ?''',(pat.upper(),))
for r in cur.fetchall():
    print(r)

print('\nAccess logs matching normalized_patente:')
cur.execute('''SELECT id, patente_detectada, normalized_patente, tipo_evento, fecha_hora, pago_confirmado, reserva_id, sucursal, costo_estadia FROM access_logs WHERE normalized_patente = ? ORDER BY id DESC''',(norm,))
for r in cur.fetchall():
    print(r)

print('\nLast 20 access_logs overall (for quick scan):')
cur.execute('SELECT id, patente_detectada, normalized_patente, tipo_evento, fecha_hora, pago_confirmado, reserva_id, sucursal FROM access_logs ORDER BY id DESC LIMIT 20')
for r in cur.fetchall():
    print(r)

conn.close()
