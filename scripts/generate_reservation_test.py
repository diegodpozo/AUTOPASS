"""Genera movimientos completos de reservas AUTOPASS de forma automatizada.

Con solo nombrar la tanda se crean N movimientos (reserva + pago + entrada + salida)
sobre los 40 usuarios pruebaoc, repartidos entre las 5 sucursales y los modos, se abonan
con saldo, se simulan los ingresos manuales por sucursal, se verifica la ocupacion durante
la estadia y se efectua el egreso, quedando todas las reservas COMPLETADA.

Fechas: SOLO pasadas. La ventana valida es [PAST_START (01-09-2026), hoy): ningun movimiento
puede quedar en el futuro, ni antes del 01-09-2026. El modo "hora" se excluye porque el
sistema exige anticipacion minima y no admite fechas pasadas.

Acumulativo: nunca borra. Cada corrida agrega N movimientos nuevos en espacios libres,
evitando repetir ventanas ya usadas. Entorno de pruebas: Arduino/barrea (MQTT+USB serial)
y notificaciones quedan deshabilitados; el tiempo virtual se restaura al terminar.

Uso:
    python scripts/generate_reservation_test.py NOMBRE -n 10            # 10 movimientos
    python scripts/generate_reservation_test.py NOMBRE -n 30 --solo-plan # solo muestra el plan
"""

import argparse
import datetime
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from collections import Counter

from core.database import SessionLocal
from core.normalize import normalize_plate
from models import AccessLog, User
from models.enums import AccessEventType, PaymentStatus, ReservationStatus
from models.notification import UserNotification
from models.reservation import Reservation
from repositories.access_log_repository import AccessRepository
from repositories.branch_repository import BranchRepository
from repositories.vehicle_repository import VehicleRepository
from schemas.reservation import UserReservationCreate
from sqlalchemy import or_
from services.access_service import AccessService
from services.availability import capacidad_reservas
from services.email_service import EmailService
from services.hardware_service import HardwareService
from services.notification_service import NotificationService
from services.payments import ReservationPaymentsMixin
from services.reservation_service import ReservationService
from services.time_service import TimeService

MODES = ["hora", "dia", "semana", "quincena", "mes"]
PLAN_MODES = ["dia", "semana", "quincena", "mes"]  # "hora" exige anticipacion minima: no admite fechas pasadas
DUR_DAYS = {"hora": 0.0833, "dia": 1, "semana": 7, "quincena": 15, "mes": 30}
DAY_START = datetime.time(13, 0)
PAST_START = datetime.date(2026, 9, 1)  # nunca generar pruebas anteriores a esta fecha
# Tiempo virtual previo a la ventana: mientras se crean/abonan las reservas pasadas, el server
# en marcha (puerto 8000) trae workers que auto-finalizan/auto-cancelan reservas vencidas
# (WorkerService + ReservationService.auto_finalize_all_reservations/cleanup_overdue_reservations).
# Con "ahora" anterior al inicio de la ventana, esas reservas se ven como futuras y no se tocan.
CREATE_SAFE_DT = datetime.datetime(2026, 8, 31, 0, 0)
TIPOS = ("Auto", "Moto", "Camioneta")
PRUEBAOC_PATTERN = "%@pruebaoc.com"
SNAPSHOT_DIR = os.path.join(ROOT, "data", "pruebas")


def _snapshot_path(name: str) -> str:
    return os.path.join(SNAPSHOT_DIR, f"{name}.json")


def _validar_nombre(name: str) -> str:
    if not re.fullmatch(r"[a-z0-9_-]{1,40}", name):
        sys.exit(f"Nombre de prueba invalido: '{name}'. Use [a-z0-9_-], sin espacios ni caracteres especiales.")
    return name


def _branch_names(db) -> list:
    return [b.nombre for b in BranchRepository.get_all(db)]


def _user_tipo(u) -> str:
    if hasattr(u, "vehicles") and u.vehicles:
        v = u.vehicles[0]
        return v.tipo.value if hasattr(v.tipo, "value") else str(v.tipo)
    return "Auto"


def _seed_ocupacion(db, pid, wstart, wend):
    """Ocupacion base y ventanas ya usadas por los usuarios de prueba en [wstart, wend].

    - occ: reservas ACTIVA/PENDIENTE de TODOS (capacidad real de cada ventana).
    - busy: TODAS las reservas (cualquier estado) de los usuarios de prueba, para que
      los movimientos nuevos no repitan una ventana ya usada.
    Devuelve (occ, busy): occ por (sucursal, tipo) y busy por user_id.
    """
    lo = wstart.strftime("%Y-%m-%d 00:00:00")
    hi = wend.strftime("%Y-%m-%d 23:59:59")
    res_act = db.query(Reservation).filter(
        Reservation.fecha_inicio < hi, Reservation.fecha_fin > lo,
        Reservation.estado_reserva.in_([ReservationStatus.PENDIENTE.value, ReservationStatus.ACTIVA.value]),
        Reservation.estado_pago.in_([PaymentStatus.PENDIENTE.value, PaymentStatus.PAGADO.value]),
    ).all()
    res_all = db.query(Reservation).filter(
        Reservation.fecha_inicio < hi, Reservation.fecha_fin > lo,
        Reservation.user_id.in_(pid),
    ).all()
    vmap = VehicleRepository.get_tipos_by_patentes(
        db, list({r.patente for r in res_act} | {r.patente for r in res_all}))

    def _ival(r):
        try:
            return (datetime.datetime.fromisoformat(r.fecha_inicio),
                    datetime.datetime.fromisoformat(r.fecha_fin))
        except Exception:
            return None

    def _tipo(r):
        return vmap.get(normalize_plate(r.patente), r.tipo_vehiculo or "Auto") or "Auto"

    occ, busy = {}, {}
    for r in res_act:
        iv = _ival(r)
        if iv:
            occ.setdefault(r.sucursal_nombre, {}).setdefault(_tipo(r), []).append(iv)
    for r in res_all:
        iv = _ival(r)
        if iv:
            busy.setdefault(r.user_id, []).append(iv)
    return occ, busy


# ---------------------------------------------------------------------------
# 1. PLAN
# ---------------------------------------------------------------------------
def build_plan(db, movimientos):
    branches = BranchRepository.get_all(db)
    branch_names = [b.nombre for b in branches]
    users = sorted(
        (u for u in db.query(User).filter(User.email.like(PRUEBAOC_PATTERN)).all()),
        key=lambda u: u.id,
    )

    CAP = {b.nombre: {t: capacidad_reservas(db, b.nombre, t) for t in TIPOS} for b in branches}
    WEND = datetime.datetime.now()

    def new_occ(seed):
        return {b.nombre: {t: list(seed.get(b.nombre, {}).get(t, [])) for t in TIPOS} for b in branches}

    def best_start(user, bname, mode, tipo, o, bu, CAP):
        """Inicio mas reciente valido en [PAST_START, WEND) con fin tambien en el pasado."""
        day = WEND.date()
        for k in range(0, (WEND.date() - PAST_START).days + 1):
            base = day - datetime.timedelta(days=k)
            if base < PAST_START:
                break
            start_dt = datetime.datetime.combine(base, DAY_START)
            end_dt = start_dt + datetime.timedelta(days=DUR_DAYS[mode])
            if end_dt > WEND:
                continue
            if sum(1 for (s, e) in o[bname][tipo] if s < end_dt and e > start_dt) >= CAP[bname][tipo]:
                continue
            if any(s < end_dt and e > start_dt for (s, e) in bu[user.id]):
                continue
            return start_dt
        return None

    seed, busy_seed = _seed_ocupacion(db, [u.id for u in users], PAST_START, WEND)
    occ = new_occ(seed)
    busy = {u.id: list(busy_seed.get(u.id, [])) for u in users}

    # Coloca N movimientos ciclando usuarios, sucursales y modos hasta agotar cupo.
    plan, r = [], 0
    while len(plan) < movimientos:
        progreso = False
        for i, u in enumerate(users):
            if len(plan) >= movimientos:
                break
            bname = branch_names[(i + r) % len(branch_names)]
            mode = PLAN_MODES[(i + r) % len(PLAN_MODES)]
            tipo = _user_tipo(u)
            sd = best_start(u, bname, mode, tipo, occ, busy, CAP)
            if sd is None:
                continue
            end_dt = sd + datetime.timedelta(days=DUR_DAYS[mode])
            occ[bname][tipo].append((sd, end_dt))
            busy[u.id].append((sd, end_dt))
            plan.append((u, bname, mode, tipo, sd, end_dt))
            progreso = True
        if not progreso:
            break
        r += 1

    unplaced = [("sin-lugar", "", "", "")] * (movimientos - len(plan))
    return {"plan": plan, "occ": occ, "users": users, "branch_names": branch_names, "unplaced": unplaced, "CAP": CAP}


def _print_plan(plan_obj):
    plan, branch_names, unplaced, CAP = plan_obj["plan"], plan_obj["branch_names"], plan_obj["unplaced"], plan_obj["CAP"]
    print(f"USUARIOS: {len(plan_obj['users'])} | PLANEADAS: {len(plan)} | SIN LUGAR: {len(unplaced)}")
    cm, ci = Counter((p[1], p[2]) for p in plan), Counter((p[1], p[3]) for p in plan)
    print("\n== COBERTURA (sucursal x modo) ==")
    for b in branch_names:
        print(" ", b, {m: cm.get((b, m), 0) for m in PLAN_MODES})
    print("\n== CANTIDADES (sucursal x tipo) ==")
    for b in branch_names:
        for t in TIPOS:
            print(f"  {b:20s} {t:10s} {ci.get((b, t), 0)}  (cap={CAP[b][t]})")
    # max simultaneo del plan (incluye baseline)
    occ = plan_obj["occ"]
    for b in branch_names:
        for t in TIPOS:
            iv = sorted(occ[b][t], key=lambda x: x[0])
            evs, cur, mx = [], 0, 0
            for s, e in iv:
                evs.append((s, 1)); evs.append((e, -1))
            evs.sort(key=lambda x: (x[0], x[1]))
            for _, c in evs:
                cur += c; mx = max(mx, cur)
            flag = "OK" if mx <= CAP[b][t] else "EXCEDE"
            print(f"  max_sim {b:20s} {t:10s} {mx} cap={CAP[b][t]} {flag}")
    if unplaced:
        print("\n== SIN LUGAR ==")
        for x in unplaced:
            print(" ", x)


# ---------------------------------------------------------------------------
# 2. CREAR + ABONAR  (monkeypatch correo)
# ---------------------------------------------------------------------------
def create_and_pay(db, plan_obj):
    EmailService.send_reservation_confirmation = lambda *a, **k: None
    users = plan_obj["users"]
    by_id = {u.id: u for u in users}
    total = len(plan_obj["plan"])
    created = paid = credited = skipped = 0
    failures, reservas = [], []
    for n, (u, bname, mode, tipo, sd, ed) in enumerate(plan_obj["plan"], 1):
        if n % 25 == 0 or n == total:
            print(f"  [{n}/{total}] creadas={created} pagadas={paid} skip={skipped} "
                  f"fallos={len(failures)}", flush=True)
        user = by_id[u.id]
        patente = u.vehicles[0].patente if u.vehicles else None
        if not patente:
            failures.append((u.id, bname, mode, "usuario sin vehiculo"))
            continue
        ini, fin = sd.strftime("%Y-%m-%d %H:%M:%S"), ed.strftime("%Y-%m-%d %H:%M:%S")
        exist = db.query(Reservation).filter(
            Reservation.user_id == u.id, Reservation.patente == normalize_plate(patente),
            Reservation.fecha_inicio == ini, Reservation.fecha_fin == fin).order_by(Reservation.id.desc()).first()
        if exist:
            # ya existe (misma prueba regenerada o corrida previa): se toma tal cual
            skipped += 1
            reservas.append(exist)
            continue
        data = UserReservationCreate(patente=patente, fecha_inicio=ini, fecha_fin=fin,
                                     sucursal_nombre=bname, tipo_estadia=mode)
        try:
            res_d = ReservationService.create_user_reservation(db, user, data)
        except Exception as e:
            msg = getattr(e, "detail", None) or str(e)
            failures.append((u.id, bname, mode, ini, f"CREATE: {msg}"))
            db.rollback()
            continue
        created += 1
        res = db.query(Reservation).filter(
            Reservation.user_id == u.id, Reservation.patente == normalize_plate(patente),
            Reservation.fecha_inicio == ini, Reservation.fecha_fin == fin).order_by(Reservation.id.desc()).first()
        if res is None:
            failures.append((u.id, bname, mode, ini, "reserva creada no encontrada"))
            continue
        reservas.append(res)
        if user.saldo < res.monto_total:
            user.saldo = res.monto_total
            db.commit()
            credited += 1
        try:
            ReservationPaymentsMixin.pay_reservation(db, user, res.id)
        except Exception as e:
            msg = getattr(e, "detail", None) or str(e)
            failures.append((u.id, bname, mode, ini, f"PAY: {msg}"))
            db.rollback()
            continue
        paid += 1
    return {"creadas": created, "pagadas": paid, "acreditados": credited, "skipped": skipped,
            "fallos": failures, "reservas": reservas}


# ---------------------------------------------------------------------------
# 3. SIMULACION DE INGRESOS / ESTADIA / EGRESOS
# ---------------------------------------------------------------------------
def simulate(db, reservas):
    HardwareService.trigger_barrier = lambda *a, **k: {"status": "ok", "message": "hardware deshabilitado (pruebas)"}
    NotificationService.notify_occupancy_change = lambda db=None, sucursal_norm=None: None

    if not reservas:
        return {"entradas": 0, "salidas": 0, "skipped": 0, "fallos": ["sin reservas para simular"],
                "max_sim": {}, "por_suc": {}, "log_ids": []}

    # Idempotencia: ya cumplimentadas (COMPLETADA o con ingreso registrado) se saltan.
    ids = [r.id for r in reservas]
    con_entrada = set(AccessRepository.get_reserva_ids_with_entry(db, ids))
    cand = [r for r in reservas
            if r.estado_reserva in (ReservationStatus.ACTIVA, ReservationStatus.PENDIENTE)
            and r.id not in con_entrada]
    skipped = len(reservas) - len(cand)
    if skipped:
        print(f"  saltando {skipped} reservas ya procesadas (cumplidas/ingresadas)")

    if not cand:
        return {"entradas": 0, "salidas": 0, "skipped": len(reservas),
                "fallos": [], "max_sim": {}, "por_suc": {}, "log_ids": []}

    branch_names = _branch_names(db)
    CAP = {b: {t: capacidad_reservas(db, b, t) for t in TIPOS} for b in branch_names}

    events = []
    for r in cand:
        s = datetime.datetime.fromisoformat(r.fecha_inicio)
        e = datetime.datetime.fromisoformat(r.fecha_fin)
        events.append((s + datetime.timedelta(seconds=61), AccessEventType.ENTRADA, r))
        events.append((e, AccessEventType.SALIDA, r))
    events.sort(key=lambda x: (x[0], 0 if x[1] == AccessEventType.SALIDA else 1))

    expected = {b: {t: 0 for t in TIPOS} for b in branch_names}
    max_sim = {b: {t: 0 for t in TIPOS} for b in branch_names}
    por_suc = {b: {"ENTRADA": 0, "SALIDA": 0} for b in branch_names}
    failures, log_ids, ok_in, ok_out = [], [], 0, 0
    orig_offset = TimeService.get_offset()

    for i, (dt, ev, res) in enumerate(events, 1):
        TimeService.set_target_datetime(dt)
        branch, tipo = res.sucursal_nombre, res.tipo_vehiculo or "Auto"
        expected[branch][tipo] = max(expected[branch][tipo] + (1 if ev == AccessEventType.ENTRADA else -1), 0)
        max_sim[branch][tipo] = max(max_sim[branch][tipo], expected[branch][tipo])
        try:
            if ev == AccessEventType.ENTRADA:
                AccessService.manual_entry(db, res.patente, branch, tipo_vehiculo=tipo)
                last = AccessRepository.get_last_entry(db, normalize_plate(res.patente), branch)
                if last is None or last.reserva_id != res.id:
                    failures.append((res.id, branch, tipo, "ENTRADA no vinculada a reserva"))
                else:
                    ok_in += 1; por_suc[branch]["ENTRADA"] += 1; log_ids.append(last.id)
            else:
                AccessService.manual_exit(db, res.patente, branch)
                last = AccessRepository.get_last_by_patente_and_sucursal(db, normalize_plate(res.patente), branch)
                if last is None or last.tipo_evento != AccessEventType.SALIDA or last.pago_confirmado is not True:
                    failures.append((res.id, branch, tipo, "SALIDA no registrada"))
                else:
                    ok_out += 1; por_suc[branch]["SALIDA"] += 1; log_ids.append(last.id)
        except Exception as e:
            msg = getattr(e, "detail", None) or str(e)
            failures.append((res.id, branch, tipo, f"{ev}: {msg}"))
            db.rollback()
            expected[branch][tipo] = max(expected[branch][tipo] - (1 if ev == AccessEventType.ENTRADA else -1), 0)
        if i % 50 == 0 or i == len(events):
            print(f"  [{i}/{len(events)}] vnow={TimeService.now_str()} in={ok_in} out={ok_out}", flush=True)

    TimeService.set_offset(orig_offset)
    return {"entradas": ok_in, "salidas": ok_out, "skipped": skipped, "fallos": failures, "max_sim": max_sim,
            "por_suc": por_suc, "log_ids": log_ids, "CAP": CAP}


# ---------------------------------------------------------------------------
# 4. FINALIZACION (solo las reservas de la prueba)
# ---------------------------------------------------------------------------
def finalize(db, reservas):
    if not reservas:
        return 0
    max_fin = max(datetime.datetime.fromisoformat(r.fecha_fin) for r in reservas)
    TimeService.set_target_datetime(max_fin + datetime.timedelta(days=1))
    ids = [r.id for r in reservas]
    filas = db.query(Reservation).filter(Reservation.id.in_(ids)).all()
    for r in filas:
        r.estado_reserva = ReservationStatus.COMPLETADA
    db.commit()
    TimeService.set_offset(0)
    return len(filas)


# ---------------------------------------------------------------------------
# 5. SNAPSHOT / LIMPIEZA
# ---------------------------------------------------------------------------
def _limpiar(db, name):
    spath = _snapshot_path(name)
    if not os.path.exists(spath):
        print(f"No existe snapshot de la prueba '{name}' (nada que limpiar).")
        return
    with open(spath, encoding="utf-8") as f:
        snap = json.load(f)

    ids_logs = snap.get("access_log_ids", [])
    ids_res = [r["id"] for r in snap.get("reservas", [])]
    patentes = {normalize_plate(r.get("patente", "")) for r in snap.get("reservas", []) if r.get("patente")}
    n_log = 0
    if ids_logs:
        n_log += db.query(AccessLog).filter(AccessLog.id.in_(ids_logs)).delete(synchronize_session=False)
    conds = []
    if ids_res:
        conds.append(AccessLog.reserva_id.in_(ids_res))
    if patentes:
        conds.append(AccessLog.normalized_patente.in_(list(patentes)))
    if conds:
        n_log += db.query(AccessLog).filter(or_(*conds)).delete(synchronize_session=False)
    if ids_res:
        db.query(UserNotification).filter(UserNotification.reserva_id.in_(ids_res)).delete(synchronize_session=False)
        n_res = db.query(Reservation).filter(Reservation.id.in_(ids_res)).delete(synchronize_session=False)
    else:
        n_res = 0

    for uid, saldo in (snap.get("saldos_iniciales", {}) or {}).items():
        u = db.query(User).filter(User.id == int(uid)).first()
        if u:
            u.saldo = saldo

    for b in _branch_names(db):
        af = BranchRepository.get_aforo_by_sucursal(db, b)
        if af:
            af.ocupacion_reservas = af.ocupacion_reservas_autos = af.ocupacion_reservas_motos = \
                af.ocupacion_reservas_camionetas = 0
    db.commit()
    os.remove(spath)
    print(f"Limpieza de '{name}': reservas borradas={n_res} access_logs borrados={n_log} saldos restaurados.")


# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------
def run(db, name, movimientos=10, only_plan=False):
    print("== 1/4 PLAN ==")
    plan_obj = build_plan(db, movimientos)
    _print_plan(plan_obj)
    if only_plan:
        return
    if len(plan_obj["plan"]) < movimientos:
        print(f"!! Solo se pudieron ubicar {len(plan_obj['plan'])} de {movimientos} movimientos "
              f"(sin lugar: {len(plan_obj['unplaced'])}); abortando sin escribir.")
        return

    db.expire_all()
    saldos_iniciales = {u.id: u.saldo for u in
                        db.query(User).filter(User.email.like(PRUEBAOC_PATTERN)).all()}

    print("\n== 2/4 CREAR + ABONAR ==")
    # Se mantiene el tiempo virtual en pre-ventana hasta la simulacion (que fija "ahora" en cada
    # evento); asi los workers del server no ven las reservas como vencidas y no las tocan.
    TimeService.set_target_datetime(CREATE_SAFE_DT)
    c = create_and_pay(db, plan_obj)
    print(f"  creadas={c['creadas']} pagadas={c['pagadas']} acreditados={c['acreditados']} "
          f"ya-existentes(skip)={c['skipped']} fallos={len(c['fallos'])}")
    for f in c["fallos"]:
        print("  FALLO:", f)
    if c["reservas"]:
        _ids = [r.id for r in c["reservas"]]
        _st = Counter(r.estado_reserva.value if hasattr(r.estado_reserva, "value") else str(r.estado_reserva)
                      for r in db.query(Reservation).filter(Reservation.id.in_(_ids)).all())
        print(f"  estado tras crear/abonar (debe ser {{'Activa': {len(_ids)}}}): {dict(_st)}")

    print("\n== 3/4 SIMULACION (ingresos/estadia/egresos) ==")
    s = simulate(db, c["reservas"])
    print(f"  entradas={s['entradas']} salidas={s['salidas']} fallos={len(s['fallos'])}")
    for f in s["fallos"]:
        print("  FALLO:", f)

    print("\n== POR SUCURSAL (admin simulado) ==")
    for b, v in s["por_suc"].items():
        print(f"  {b:20s} ingresos={v['ENTRADA']} egresos={v['SALIDA']}")

    print("\n== 4/4 FINALIZAR ==")
    fin = finalize(db, c["reservas"])
    print(f"  reservas COMPLETADA: {fin}")

    saldos_finales = {u.id: u.saldo for u in
                      db.query(User).filter(User.email.like(PRUEBAOC_PATTERN)).all()}

    # ---- REPORTE ----
    print("\n== ESTADO FINAL RESERVAS ==")
    ids = [r.id for r in c["reservas"]]
    st = db.query(Reservation).filter(Reservation.id.in_(ids)).all()
    cs = Counter(r.estado_reserva.value if hasattr(r.estado_reserva, "value") else str(r.estado_reserva) for r in st)
    cp = Counter(r.estado_pago.value if hasattr(r.estado_pago, "value") else str(r.estado_pago) for r in st)
    print(f"  total={len(st)} estado_reserva={dict(cs)} estado_pago={dict(cp)}")

    print("\n== MAX SIMULTANEO usado vs capacidad ==")
    cap_ok = True
    for b, tipos in s["max_sim"].items():
        for t in TIPOS:
            mx, cap = tipos[t], s["CAP"][b][t]
            if mx > cap:
                cap_ok = False
            print(f"  {b:20s} {t:10s} max={mx} cap={cap} {'OK' if mx <= cap else 'EXCEDE'}")

    # ---- SNAPSHOT ----
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    snap = {
        "nombre": name,
        "movimientos": movimientos,
        "generado": datetime.datetime.now().isoformat(),
        "saldos_iniciales": {str(k): v for k, v in saldos_iniciales.items()},
        "saldos_finales": {str(k): v for k, v in saldos_finales.items()},
        "reservas": [{"id": r.id, "user_id": r.user_id, "patente": r.patente,
                      "sucursal": r.sucursal_nombre, "modo": r.tipo_estadia,
                      "inicio": r.fecha_inicio, "fin": r.fecha_fin} for r in c["reservas"]],
        "access_log_ids": s["log_ids"],
        "cobertura": {b: {m: sum(1 for r in c["reservas"] if r.sucursal_nombre == b and r.tipo_estadia == m)
                          for m in PLAN_MODES} for b in s["por_suc"]},
    }
    with open(_snapshot_path(name), "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)

    print(f"\nRESULTADO '{name}': movimientos={s['entradas']} creadas={c['creadas']} pagadas={c['pagadas']} "
          f"entradas={s['entradas']} salidas={s['salidas']} saltadas(ya-procesadas)={s['skipped']} "
          f"fallos={len(c['fallos']) + len(s['fallos'])} "
          f"capacidad_ok={cap_ok} finalizadas={fin}")
    print(f"Snapshot guardado en {_snapshot_path(name)}")


def main():
    ap = argparse.ArgumentParser(
        description="Genera movimientos completos de reservas AUTOPASS (reserva + pago + entrada + salida).")
    ap.add_argument("nombre", help="Nombre/label de la tanda (snake_case, sin espacios)")
    ap.add_argument("-n", "--movimientos", type=int, default=10,
                    help="Cantidad de movimientos completos a generar (default: 10)")
    ap.add_argument("--solo-plan", action="store_true", help="Solo mostrar el plan, sin escribir en la BD")
    ap.add_argument("--limpiar", action="store_true", help="(NO usar: borra datos) Borra lo registrado en esa tanda")
    args = ap.parse_args()

    _validar_nombre(args.nombre)
    if args.movimientos < 1:
        sys.exit("--movimientos debe ser >= 1")
    db = SessionLocal()
    try:
        if args.limpiar:
            _limpiar(db, args.nombre)
        else:
            run(db, args.nombre, movimientos=args.movimientos, only_plan=args.solo_plan)
    finally:
        db.close()
        TimeService.set_offset(0)


if __name__ == "__main__":
    main()