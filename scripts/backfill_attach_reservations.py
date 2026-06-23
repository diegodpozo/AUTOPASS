import sqlite3, re
DB='parking.db'
conn=sqlite3.connect(DB)
cur=conn.cursor()
cur.execute("SELECT id, patente, fecha_inicio, fecha_fin, sucursal_nombre FROM reservations WHERE estado_pago='Pagado' AND estado_reserva IN ('Pendiente','Activa')")
res = cur.fetchall()
print('Found paid active reservations:', len(res))
updated=0
for r in res:
    rid, patente, inicio, fin, suc = r
    norm = re.sub(r'[^A-Z0-9]','', (patente or '').upper())
    print('Reservation', rid, patente, 'norm', norm, 'sucursal', suc)
    # update access_logs where normalized_patente matches, reserva_id IS NULL and tipo_evento == 'ENTRADA' and fecha_hora between inicio and fin
    cur.execute("SELECT id, fecha_hora FROM access_logs WHERE normalized_patente=? AND tipo_evento='ENTRADA' AND (reserva_id IS NULL) AND sucursal=?", (norm, suc))
    rows = cur.fetchall()
    for row in rows:
        aid, fh = row
        # try simple string compare: if inicio <= fh <= fin (normalize formats)
        try:
            if inicio and fin:
                # convert to comparable substrings
                fh_s = fh.replace('T',' ').split('.')[0]
                if inicio <= fh_s <= fin:
                    cur.execute('UPDATE access_logs SET reserva_id=?, pago_confirmado=1 WHERE id=?', (rid, aid))
                    updated += 1
                    print('Updated access_log', aid, '-> reserva', rid)
        except Exception as e:
            print('compare error', e, aid, fh)

conn.commit()
print('Total updated', updated)
conn.close()
