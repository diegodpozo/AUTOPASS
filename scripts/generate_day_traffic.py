"""Genera un DIA COMPLETO de trafico de estacionamiento con RESERVAS POR HORA.

Simula, para CADA sucursal, N entradas y N salidas (default 50/50) repartidas a lo
largo de TODO el dia de HOY, reservando por hora (estadias de 1h o 2h), abonando con
el saldo de los usuarios pruebaoc (se acredita lo necesario) y registrando el ingreso
y el egreso con el flujo real del servicio de accesos.

RELoj VIRTUAL: la validacion de reservas por hora exige anticipacion minima, asi que el
script mueve un reloj en-proceso (parchea datetime.datetime y TimeService) para "viajar"
por las horas de hoy: por cada reserva, crea+paga con "ahora" = inicio - 31 min, luego
ingresa en inicio+61s y egresa en fin, quedando la reserva COMPLETADA. Asi se respeta el
tope de 5 reservas activas/pendientes por usuario sin crear cuentas nuevas.

Idempotente por nombre de tanda: si existe el snapshot, primero borra lo que genero esa
misma tanda (reservas + access_logs + notificaciones) y restaura saldos, luego regenera.

Uso:
    python scripts/generate_day_traffic.py NOMBRE                 # 50 por sucursal, hoy
    python scripts/generate_day_traffic.py NOMBRE --por-suc 50
    python scripts/generate_day_traffic.py NOMBRE --solo-plan     # solo muestra el plan
    python scripts/generate_day_traffic.py NOMBRE --limpiar       # borra la tanda y restaura saldos
"""

import argparse
import datetime as _dt
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from collections import Counter, defaultdict

from core.config import settings
from core.database import SessionLocal
from core.normalize import normalize_name, normalize_plate
from models import AccessLog, User
from models.enums import AccessEventType, PaymentStatus, ReservationStatus
from models.notification import UserNotification
from models.reservation import Reservation
from repositories.access_log_repository import AccessRepository
from repositories.branch_repository import BranchRepository
from repositories.vehicle_repository import VehicleRepository
from schemas.reservation import UserReservationCreate
from services.access_service import AccessService
from services.availability import capacidad_reservas
from services.email_service import EmailService
from services.hardware_service import HardwareService
from services.notification_service import NotificationService
from services.payments import ReservationPaymentsMixin
from services.reservation_service import ReservationService
from services.time_service import TimeService

PRUEBAOC_PATTERN = "%@pruebaoc.com"
SNAPSHOT_DIR = os.path.join(ROOT, "data", "pruebas")
TIPOS = ("Auto", "Moto", "Camioneta")

# Ventana horaria util (los 24h quedan cubiertos; las no-24h abren 07:00 y cierran 23:00/00:00)
HORA_APERTURA = 7
HORA_ULTIMO_INICIO = 22   # ultimo slot que puede iniciarse (23:00 tomado como cierre)
ANTICIPACION_MIN = 31     # minutos antes del inicio para "crear" la reserva (margen sobre el minimo)
KEEP_ACTIVE_MAX = 5       # tope del sistema de reservas activas/pendientes por usuario
SALDO_CARGA = 100000.0    # saldo inicial que se acredita a cada usuario pruebaoc para pagar las reservas

# ---------------------------------------------------------------------------
# RELOJ VIRTUAL EN-PROCESO
# ---------------------------------------------------------------------------
# datetime.datetime.now() es lo que usan: ReservationService (anticipacion), BillingService,
# payments, AccessLog, etc. Parcheamos la clase datetime.datetime del modulo compartido para
# que now() honre un offset, igual que hace TimeService con AccessService.
_real_datetime = _dt.datetime
_clock_offset = _dt.timedelta(0)


class _VirtualDateTime(_real_datetime):
    @classmethod
    def now(cls, tz=None):
        base = _real_datetime.now(tz) if tz is not None else _real_datetime.now()
        if tz is None:
            return base + _clock_offset
        return base + _clock_offset

    @classmethod
    def utcnow(cls):
        return _real_datetime.utcnow() + _clock_offset


def _install_clock():
    _dt.datetime = _VirtualDateTime


def _set_clock(target: _dt.datetime):
    """Fija el reloj virtual a una fecha/hora exacta (afecta datetime.datetime.now y TimeService)."""
    global _clock_offset
    _clock_offset = target - _real_datetime.now()
    TimeService.set_target_datetime(target)


def _now_virtual() -> _dt.datetime:
    return _real_datetime.now() + _clock_offset


# ---------------------------------------------------------------------------
# SNAPSHOT / LIMPIEZA
# ---------------------------------------------------------------------------
def _snapshot_path(name: str) -> str:
    return os.path.join(SNAPSHOT_DIR, f"{name}.json")


def _validar_nombre(name: str) -> str:
    if not re.fullmatch(r"[a-z0-9_-]{1,40}", name):
        sys.exit(f"Nombre de tanda invalido: '{name}'. Use [a-z0-9_-], sin espacios ni caracteres especiales.")
    return name


def _branch_names(db) -> list:
    return [b.nombre for b in BranchRepository.get_all(db) if b.activa]


def _saneo_entradas_abiertas(db, patentes):
    """Cierra entradas abiertas previas (ultima ENTRADA sin SALIDA posterior) por patente+sucursal.

    `manual_entry` interpreta una entrada abierta de la misma patente/sucursal como "vehiculo ya
    adentro" y omite crear el ingreso; eso descuadra la simulacion. Se agrega una SALIDA 1s despues
    de cada entrada abierta. Devuelve la cantidad de entradas cerradas.
    """
    patentes = {normalize_plate(p) for p in patentes}
    grupos = defaultdict(list)
    for l in db.query(AccessLog).all():
        if normalize_plate(l.patente_detectada or "") in patentes:
            grupos[(normalize_plate(l.patente_detectada or ""), l.sucursal_id)].append(l)
    cerradas = 0
    for (_, suc_id), logs in grupos.items():
        logs.sort(key=lambda x: (x.fecha_hora or "", x.id))
        last_e = None
        for l in logs:
            if l.tipo_evento == "ENTRADA":
                last_e = l
            elif l.tipo_evento == "SALIDA" and last_e is not None:
                last_e = None
        if last_e is not None:
            base = _dt.datetime.strptime((last_e.fecha_hora or "")[:19], "%Y-%m-%d %H:%M:%S")
            db.add(AccessLog(
                patente_detectada=last_e.patente_detectada,
                normalized_patente=last_e.normalized_patente,
                tipo_evento="SALIDA",
                tipo_vehiculo=last_e.tipo_vehiculo,
                fecha_hora=(base + _dt.timedelta(seconds=1)).strftime("%Y-%m-%d %H:%M:%S"),
                sucursal_id=suc_id,
                reserva_id=None,
            ))
            cerradas += 1
    if cerradas:
        db.commit()
    return cerradas


def _limpiar(db, name):
    spath = _snapshot_path(name)
    if not os.path.exists(spath):
        print(f"No existe snapshot de la tanda '{name}' (nada que limpiar).")
        return
    with open(spath, encoding="utf-8") as f:
        snap = json.load(f)

    ids_logs = snap.get("access_log_ids", [])
    ids_res = [r["id"] for r in snap.get("reservas", [])]
    # Logs SALIDA de manual_exit no guardan reserva_id: se borran los que coincidan con
    # las reservas planeadas (patente + dia de inicio + sucursal), sin tocar otras tandas.
    planes = snap.get("planned", []) or []
    dias = {p["inicio"][:10] for p in planes if p.get("inicio")}
    pat_dia = {(normalize_plate(p["patente"]), p["inicio"][:10]) for p in planes
               if p.get("patente") and p.get("inicio")}
    n_log = 0
    if ids_logs:
        n_log += db.query(AccessLog).filter(AccessLog.id.in_(ids_logs)).delete(synchronize_session=False)
    if ids_res:
        n_log += db.query(AccessLog).filter(AccessLog.reserva_id.in_(ids_res)).delete(synchronize_session=False)
    # exits huerfanos: patente del plan, SIN reserva_id, en el/los dia(s) de la tanda
    if pat_dia:
        huerfanos = []
        for l in db.query(AccessLog).filter(AccessLog.reserva_id.is_(None)).all():
            key = (normalize_plate(l.patente_detectada or ""), (l.fecha_hora or "")[:10])
            if key in pat_dia:
                huerfanos.append(l.id)
        if huerfanos:
            n_log += db.query(AccessLog).filter(AccessLog.id.in_(huerfanos)).delete(synchronize_session=False)
    n_res = 0
    if ids_res:
        db.query(UserNotification).filter(UserNotification.reserva_id.in_(ids_res)).delete(synchronize_session=False)
        n_res = db.query(Reservation).filter(Reservation.id.in_(ids_res)).delete(synchronize_session=False)
    # Reservas planeadas que quedaron sin id en snapshot (corrida cortada antes de registrar id):
    # se borran por patente + inicio + sucursal de las planeadas.
    if planes:
        huerfanas_res = []
        for r in db.query(Reservation).all():
            ri = (r.fecha_inicio or "")[:19]
            for p in planes:
                if (normalize_plate(r.patente) == normalize_plate(p["patente"])
                        and ri == p["inicio"] and r.sucursal_nombre == p["sucursal"]):
                    huerfanas_res.append(r.id)
                    break
        if huerfanas_res:
            db.query(UserNotification).filter(UserNotification.reserva_id.in_(huerfanas_res)).delete(synchronize_session=False)
            n_res += db.query(Reservation).filter(Reservation.id.in_(huerfanas_res)).delete(synchronize_session=False)

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
# PLAN
# ---------------------------------------------------------------------------
def _user_tipo(u) -> str:
    if hasattr(u, "vehicles") and u.vehicles:
        v = u.vehicles[0]
        return v.tipo.value if hasattr(v.tipo, "value") else str(v.tipo)
    return "Auto"


def _slots_del_dia():
    """Inicios de hora disponibles hoy (07:00 .. 22:00)."""
    hoy = _dt.date.today()
    return [_dt.datetime.combine(hoy, _dt.time(h)) for h in range(HORA_APERTURA, HORA_ULTIMO_INICIO + 1)]


def build_plan(db, por_suc: int, seed: int):
    """Ubica `por_suc` reservas por sucursal (1h/2h) hoy respetando la capacidad simultanea.

    Devuelve reservas ordenadas por inicio, cada una con (user, branch, tipo, start, end, dur_h).
    """
    rng = random.Random(seed)
    branches = _branch_names(db)
    users = sorted(db.query(User).filter(User.email.like(PRUEBAOC_PATTERN)).all(), key=lambda u: u.id)
    if not users:
        sys.exit("No hay usuarios pruebaoc.")

    CAP = {b: {t: capacidad_reservas(db, b, t) for t in TIPOS} for b in branches}
    slots = _slots_del_dia()

    # ocupacion por (sucursal, tipo): lista de (start, end) ya colocados
    occup = defaultdict(lambda: defaultdict(list))
    # busy por usuario: intervalos (cualquier sucursal) para no solapar
    busy = defaultdict(list)

    def cabe(bname, tipo, s, e):
        cap = CAP[bname][tipo]
        if cap < 1:
            return False
        overlap = sum(1 for (os_, oe) in occup[bname][tipo] if os_ < e and oe > s)
        return overlap < cap

    def user_libre(u, s, e):
        return not any(os_ < e and oe > s for (os_, oe) in busy[u.id])

    plan = []
    # Asignacion por ronda: cada sucursal recibe por_suc reservas.
    for bname in branches:
        colocadas = 0
        # orden de slots con leve aleatoriedad para que no quede todo a las mismas horas
        slot_order = list(slots)
        rng.shuffle(slot_order)
        guard = 0
        while colocadas < por_suc and guard < 100000:
            guard += 1
            s = slot_order[guard % len(slot_order)]
            dur_h = rng.choice([1, 1, 2])  # mezcla 1h (doble peso) / 2h
            e = s + _dt.timedelta(hours=dur_h)
            if e.date() != s.date():
                continue
            # elegir un usuario con tipo de vehiculo y libre
            candidatos = [u for u in users if _user_tipo(u) and user_libre(u, s, e)]
            rng.shuffle(candidatos)
            elegido = None
            for u in candidatos:
                tipo = _user_tipo(u)
                if cabe(bname, tipo, s, e):
                    elegido = (u, tipo)
                    break
            if not elegido:
                continue
            u, tipo = elegido
            occup[bname][tipo].append((s, e))
            busy[u.id].append((s, e))
            plan.append({"user": u, "branch": bname, "tipo": tipo, "start": s, "end": e, "dur_h": dur_h})
            colocadas += 1
        if colocadas < por_suc:
            print(f"  !! {bname}: solo se pudieron ubicar {colocadas}/{por_suc} (capacidad/ventana)")

    plan.sort(key=lambda p: (p["start"], p["branch"]))
    return {"plan": plan, "branches": branches, "users": users, "CAP": CAP, "por_suc": por_suc}


def _print_plan(po):
    plan, branches = po["plan"], po["branches"]
    print(f"RESERVAS PLANEADAS: {len(plan)} | sucursales={len(branches)} | objetivo {po['por_suc']}/sucursal")
    cb = Counter(p["branch"] for p in plan)
    ct = Counter((p["branch"], p["tipo"]) for p in plan)
    cd = Counter(p["dur_h"] for p in plan)
    print("\n== POR SUCURSAL ==")
    for b in branches:
        print(f"  {b:22s} reservas={cb.get(b, 0):3d}  (cap {po['CAP'][b]})")
    print("\n== DURACION ==", dict(cd))
    print("\n== POR SUCURSAL/TIPO ==")
    for b in branches:
        print(" ", b, {t: ct.get((b, t), 0) for t in TIPOS})
    # max simultaneo por sucursal/tipo
    print("\n== MAX SIMULTANEO vs CAP ==")
    for b in branches:
        for t in TIPOS:
            iv = sorted((p["start"], p["end"]) for p in plan if p["branch"] == b and p["tipo"] == t)
            evs = []
            for s, e in iv:
                evs.append((s, 1)); evs.append((e, -1))
            evs.sort(key=lambda x: (x[0], x[1]))
            cur = mx = 0
            for _, c in evs:
                cur += c; mx = max(mx, cur)
            cap = po["CAP"][b][t]
            flag = "OK" if mx <= cap else "EXCEDE"
            if mx:
                print(f"  {b:22s} {t:10s} max={mx} cap={cap} {flag}")


# ---------------------------------------------------------------------------
# EJECUCION (crear + pagar + ingresar + egresar + finalizar) por reserva
# ---------------------------------------------------------------------------
def run(db, name, por_suc=50, seed=11, only_plan=False):
    print("== 1/5 PLAN ==")
    po = build_plan(db, por_suc, seed)
    _print_plan(po)
    plan = po["plan"]
    if only_plan:
        return
    objetivo = por_suc * len(po["branches"])
    if len(plan) < objetivo:
        print(f"!! Solo se ubicaron {len(plan)}/{objetivo} reservas; se continuara con las disponibles.")

    EmailService.send_reservation_confirmation = lambda *a, **k: None
    HardwareService.trigger_barrier = lambda *a, **k: {"status": "ok", "message": "hardware off"}
    NotificationService.notify_occupancy_change = lambda *a, **k: None

    db.expire_all()
    saldos_iniciales = {u.id: u.saldo for u in db.query(User).filter(User.email.like(PRUEBAOC_PATTERN)).all()}
    # Cargar saldo holgado para que las reservas se paguen realmente y quede remanente visible.
    usuarios_tanda = db.query(User).filter(User.email.like(PRUEBAOC_PATTERN)).all()
    for u in usuarios_tanda:
        u.saldo = SALDO_CARGA
    db.commit()
    print(f"  saldo inicial acreditado: ${SALDO_CARGA:.2f} x {len(usuarios_tanda)} usuarios.")

    print("\n== 2/5 CREAR + PAGAR + SIMULAR (reloj virtual por todo el dia) ==")
    log_ids, reservas_out = [], []
    fallos = []
    ok_in = ok_out = 0
    por_suc_count = defaultdict(lambda: {"ENTRADA": 0, "SALIDA": 0})
    orig_offset = TimeService.get_offset()

    # Saneo: cerrar entradas abiertas previas de estas patentes para que manual_entry cree el ingreso.
    pats_plan = [normalize_plate(p["user"].vehicles[0].patente) for p in plan if p["user"].vehicles]
    n_saneo = _saneo_entradas_abiertas(db, pats_plan)
    if n_saneo:
        print(f"  saneo: {n_saneo} entradas abiertas previas cerradas.")

    # Snapshot PARCIAL: se escribe desde el inicio (con las reservas planeadas) y se actualiza
    # a medida que avanza, para que una corrida interrumpida siempre sea limpiable por nombre.
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    planned_keys = [{"user_id": p["user"].id, "patente": normalize_plate(p["user"].vehicles[0].patente),
                     "sucursal": p["branch"], "inicio": p["start"].strftime("%Y-%m-%d %H:%M:%S"),
                     "fin": p["end"].strftime("%Y-%m-%d %H:%M:%S")} for p in plan if p["user"].vehicles]

    def _write_snapshot(estado):
        snap = {
            "nombre": name,
            "por_sucursal": por_suc,
            "estado": estado,
            "generado": _real_datetime.now().isoformat(),
            "saldos_iniciales": {str(k): v for k, v in saldos_iniciales.items()},
            "reservas": reservas_out,
            "planned": planned_keys,
            "access_log_ids": list(log_ids),
        }
        with open(_snapshot_path(name), "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=1)

    _write_snapshot("en_curso")

    for i, p in enumerate(plan, 1):
        u, bname, tipo = p["user"], p["branch"], p["tipo"]
        s, e = p["start"], p["end"]
        patente = u.vehicles[0].patente if u.vehicles else None
        if not patente:
            fallos.append((bname, "usuario sin vehiculo"))
            continue

        # 1) CREAR con "ahora" = inicio - anticipacion (pasa la validacion de hora)
        _set_clock(s - _dt.timedelta(minutes=ANTICIPACION_MIN))
        ini, fin = s.strftime("%Y-%m-%d %H:%M:%S"), e.strftime("%Y-%m-%d %H:%M:%S")
        exist = db.query(Reservation).filter(
            Reservation.user_id == u.id, Reservation.patente == normalize_plate(patente),
            Reservation.fecha_inicio == ini, Reservation.fecha_fin == fin).order_by(Reservation.id.desc()).first()
        res = exist
        try:
            if res is None:
                data = UserReservationCreate(patente=patente, fecha_inicio=ini, fecha_fin=fin,
                                             sucursal_nombre=bname, tipo_estadia="hora")
                ReservationService.create_user_reservation(db, u, data)
                res = db.query(Reservation).filter(
                    Reservation.user_id == u.id, Reservation.patente == normalize_plate(patente),
                    Reservation.fecha_inicio == ini, Reservation.fecha_fin == fin).order_by(Reservation.id.desc()).first()
            if res is None:
                fallos.append((u.id, bname, ini, "reserva no encontrada tras crear"))
                continue

            # 2) PAGAR con saldo (los usuarios arrancan con saldo holgado, no se reacredita por reserva)
            if res.estado_pago != PaymentStatus.PAGADO:
                ReservationPaymentsMixin.pay_reservation(db, u, res.id)
            reservas_out.append({"id": res.id, "user_id": res.user_id, "patente": res.patente,
                                 "sucursal": bname, "inicio": res.fecha_inicio, "fin": res.fecha_fin})

            # 3) INGRESO en inicio + 61s
            _set_clock(s + _dt.timedelta(seconds=61))
            AccessService.manual_entry(db, res.patente, bname, tipo_vehiculo=tipo)
            last = AccessRepository.get_last_entry(db, normalize_plate(res.patente), bname)
            if last is None or last.reserva_id != res.id:
                fallos.append((res.id, bname, ini, "ENTRADA no vinculada a reserva"))
            else:
                ok_in += 1
                por_suc_count[bname]["ENTRADA"] += 1
                log_ids.append(last.id)

            # 4) EGRESO en fin de la reserva
            _set_clock(e)
            AccessService.manual_exit(db, res.patente, bname)
            last = AccessRepository.get_last_by_patente_and_sucursal(db, normalize_plate(res.patente), bname)
            if last is None or last.tipo_evento != AccessEventType.SALIDA:
                fallos.append((res.id, bname, ini, "SALIDA no registrada"))
            else:
                ok_out += 1
                por_suc_count[bname]["SALIDA"] += 1
                log_ids.append(last.id)

            # 5) CERRAR la reserva para liberar el cupo de activas del usuario
            r2 = db.query(Reservation).filter(Reservation.id == res.id).first()
            if r2 and r2.estado_reserva not in (ReservationStatus.CANCELADA, ReservationStatus.COMPLETADA):
                r2.estado_reserva = ReservationStatus.COMPLETADA
                db.commit()
        except Exception as ex:
            msg = getattr(ex, "detail", None) or str(ex)
            fallos.append((u.id, bname, ini, f"{type(ex).__name__}: {msg}"))
            db.rollback()

        if i % 25 == 0 or i == len(plan):
            print(f"  [{i}/{len(plan)}] in={ok_in} out={ok_out} fallos={len(fallos)} "
                  f"vnow={_now_virtual().strftime('%H:%M')}", flush=True)
            _write_snapshot("en_curso")

    TimeService.set_offset(orig_offset)
    _write_snapshot("completo")

    print("\n== 3/5 POR SUCURSAL ==")
    for b in po["branches"]:
        v = por_suc_count[b]
        print(f"  {b:22s} entradas={v['ENTRADA']} salidas={v['SALIDA']}")

    print("\n== 4/5 FALLOS ==")
    print("  total fallos:", len(fallos))
    for f in fallos[:30]:
        print("  FALLO:", f)

    # ---- SNAPSHOT FINAL ----
    db.expire_all()
    saldos_finales = {u.id: u.saldo for u in db.query(User).filter(User.email.like(PRUEBAOC_PATTERN)).all()}
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)
    ids = [r["id"] for r in reservas_out]
    snap = {
        "nombre": name,
        "por_sucursal": por_suc,
        "estado": "completo",
        "generado": _real_datetime.now().isoformat(),
        "saldos_iniciales": {str(k): v for k, v in saldos_iniciales.items()},
        "saldos_finales": {str(k): v for k, v in saldos_finales.items()},
        "reservas": reservas_out,
        "planned": planned_keys,
        "access_log_ids": list(log_ids),
    }
    with open(_snapshot_path(name), "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=1)

    print("\n== 5/5 RESULTADO ==")
    print(f"  reservas={len(ids)} entradas={ok_in} salidas={ok_out} fallos={len(fallos)}")
    print(f"  snapshot: {_snapshot_path(name)}")


def main():
    ap = argparse.ArgumentParser(description="Genera un dia completo de reservas por hora + entradas/salidas.")
    ap.add_argument("nombre", help="Nombre de la tanda (snake_case, sin espacios)")
    ap.add_argument("--por-suc", type=int, default=50, help="Entradas+salidas por sucursal (default 50)")
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--solo-plan", action="store_true")
    ap.add_argument("--limpiar", action="store_true", help="Borra la tanda y restaura saldos")
    args = ap.parse_args()

    _validar_nombre(args.nombre)
    _install_clock()
    db = SessionLocal()
    try:
        if args.limpiar:
            _limpiar(db, args.nombre)
        else:
            run(db, args.nombre, por_suc=args.por_suc, seed=args.seed, only_plan=args.solo_plan)
    finally:
        db.close()
        TimeService.set_offset(0)


if __name__ == "__main__":
    main()
