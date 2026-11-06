import datetime
from typing import Dict
from sqlalchemy.orm import Session
import models
from core.logger import get_logger
from models.types import MONEY_ZERO, parse_fecha
from services.billing_service import BillingService
from services.time_service import TimeService
from models.enums import PaymentStatus, ReservationStatus
from core.normalize import normalize_name
from repositories.access_log_repository import AccessRepository
from repositories.branch_repository import BranchRepository
from repositories.reservation_repository import ReservationRepository
from repositories.settings_repository import SettingsRepository

logger = get_logger("PARKING_STATUS")


class OccupancyService:
    """Servicio de ocupación y disponibilidad de sucursales (aforo planta baja + pisos,
    reservas vigentes y vehículos estacionados con deuda calculada)."""

    @staticmethod
    def ocupacion_reservas_vigentes(db: Session, sucursal_nombre: str) -> Dict[str, int]:
        """Cuenta reservas pagadas en vigencia (activas o pendientes con su horario actual)
        para descontar la plaza exclusiva de reservas en el dashboard sin depender del ALPR."""
        try:
            now_str = TimeService.now_str()
            res = ReservationRepository.get_paid_current_by_sucursal(db, sucursal_nombre, now_str)
        except Exception:
            logger.warning("[PARKING STATUS] Error calculando reservas vigentes", exc_info=True)
            return {"autos": 0, "motos": 0, "camionetas": 0}

        conteo = {"autos": 0, "motos": 0, "camionetas": 0}
        for r in res:
            t = (r.tipo_vehiculo or "Auto").strip().lower()
            if "moto" in t:
                conteo["motos"] += 1
            elif "camioneta" in t:
                conteo["camionetas"] += 1
            else:
                conteo["autos"] += 1
        return conteo

    @staticmethod
    def default_capacities() -> Dict:
        """Capacidades por defecto (sin datos de aforo ni sucursal)."""
        return {
            "capacidad_total": 20, "ocupacion_actual": 0, "disponibilidad": 20,
            "capacidad_motos": 10, "ocupacion_motos": 0, "disponibilidad_motos": 10,
            "capacidad_camionetas": 5, "ocupacion_camionetas": 0, "disponibilidad_camionetas": 5,
            "capacidad_reservas": 0, "ocupacion_reservas": 0, "disponibilidad_reservas": 0,
            "capacidad_reservas_autos": 0, "ocupacion_reservas_autos": 0, "disponibilidad_reservas_autos": 0,
            "capacidad_reservas_motos": 0, "ocupacion_reservas_motos": 0, "disponibilidad_reservas_motos": 0,
            "capacidad_reservas_camionetas": 0, "ocupacion_reservas_camionetas": 0, "disponibilidad_reservas_camionetas": 0,
        }

    @staticmethod
    def capacities_from_aforo(a: models.ParkingAforo) -> Dict:
        """Estado de capacidad/ocupación desde un ParkingAforo sin pisos elevados."""
        cap_total = a.capacidad_total
        occ_total = a.ocupacion_actual
        cap_motos = a.capacidad_motos
        occ_motos = a.ocupacion_motos
        cap_camionetas = getattr(a, 'capacidad_camionetas', 5)
        occ_camionetas = getattr(a, 'ocupacion_camionetas', 0)
        cap_reservas = getattr(a, 'capacidad_reservas', 0)
        occ_reservas = getattr(a, 'ocupacion_reservas', 0)
        cap_res_autos = getattr(a, 'capacidad_reservas_autos', 0)
        occ_res_autos = getattr(a, 'ocupacion_reservas_autos', 0)
        cap_res_motos = getattr(a, 'capacidad_reservas_motos', 0)
        occ_res_motos = getattr(a, 'ocupacion_reservas_motos', 0)
        cap_res_camionetas = getattr(a, 'capacidad_reservas_camionetas', 0)
        occ_res_camionetas = getattr(a, 'ocupacion_reservas_camionetas', 0)

        return {
            "capacidad_total": cap_total,
            "ocupacion_actual": occ_total,
            "capacidad_motos": cap_motos,
            "ocupacion_motos": occ_motos,
            "capacidad_camionetas": cap_camionetas,
            "ocupacion_camionetas": occ_camionetas,
            "capacidad_reservas": cap_reservas,
            "ocupacion_reservas": occ_reservas,
            "capacidad_reservas_autos": cap_res_autos,
            "ocupacion_reservas_autos": occ_res_autos,
            "capacidad_reservas_motos": cap_res_motos,
            "ocupacion_reservas_motos": occ_res_motos,
            "capacidad_reservas_camionetas": cap_res_camionetas,
            "ocupacion_reservas_camionetas": occ_res_camionetas,
            "disponibilidad": cap_total - occ_total,
            "disponibilidad_motos": cap_motos - occ_motos,
            "disponibilidad_camionetas": cap_camionetas - occ_camionetas,
            "disponibilidad_reservas": max(0, cap_reservas - occ_reservas),
            "disponibilidad_reservas_autos": max(0, cap_res_autos - occ_res_autos),
            "disponibilidad_reservas_motos": max(0, cap_res_motos - occ_res_motos),
            "disponibilidad_reservas_camionetas": max(0, cap_res_camionetas - occ_res_camionetas),
        }

    @staticmethod
    def branch_by_normalized_name(db: Session, sucursal_norm: str):
        return next((b for b in BranchRepository.get_all(db)
                     if normalize_name(b.nombre) == sucursal_norm), None)

    @staticmethod
    def aforo_by_normalized_name(db: Session, sucursal_norm: str):
        return next((a for a in BranchRepository.get_all_aforos(db)
                     if a.sucursal and normalize_name(a.sucursal) == sucursal_norm), None)

    @staticmethod
    def calculate_branch_capacities(db: Session, branch: models.ParkingBranch) -> Dict:
        """Calcula capacidad y ocupación de sucursal unificando planta baja (ParkingAforo) y pisos elevados."""
        a = BranchRepository.get_aforo_by_sucursal(db, branch.nombre)
        if not a and branch.nombre:
            a = OccupancyService.aforo_by_normalized_name(db, normalize_name(branch.nombre))

        cap_autos_pb = a.capacidad_total if (a and a.capacidad_total is not None) else 20
        occ_autos_pb = a.ocupacion_actual if (a and a.ocupacion_actual is not None) else 0
        cap_motos_pb = a.capacidad_motos if (a and a.capacidad_motos is not None) else 10
        occ_motos_pb = a.ocupacion_motos if (a and a.ocupacion_motos is not None) else 0
        cap_camionetas_pb = getattr(a, 'capacidad_camionetas', 5) if (a and getattr(a, 'capacidad_camionetas', None) is not None) else 5
        occ_camionetas_pb = getattr(a, 'ocupacion_camionetas', 0) if (a and getattr(a, 'ocupacion_camionetas', None) is not None) else 0
        cap_res_autos_pb = getattr(a, 'capacidad_reservas_autos', 5) if (a and getattr(a, 'capacidad_reservas_autos', None) is not None) else 5
        occ_res_autos_pb = getattr(a, 'ocupacion_reservas_autos', 0) if (a and getattr(a, 'ocupacion_reservas_autos', None) is not None) else 0
        cap_res_motos_pb = getattr(a, 'capacidad_reservas_motos', 3) if (a and getattr(a, 'capacidad_reservas_motos', None) is not None) else 3
        occ_res_motos_pb = getattr(a, 'ocupacion_reservas_motos', 0) if (a and getattr(a, 'ocupacion_reservas_motos', None) is not None) else 0
        cap_res_camionetas_pb = getattr(a, 'capacidad_reservas_camionetas', 2) if (a and getattr(a, 'capacidad_reservas_camionetas', None) is not None) else 2
        occ_res_camionetas_pb = getattr(a, 'ocupacion_reservas_camionetas', 0) if (a and getattr(a, 'ocupacion_reservas_camionetas', None) is not None) else 0
        cap_reservas_pb = getattr(a, 'capacidad_reservas', cap_res_autos_pb + cap_res_motos_pb + cap_res_camionetas_pb) if (a and getattr(a, 'capacidad_reservas', None) is not None) else (cap_res_autos_pb + cap_res_motos_pb + cap_res_camionetas_pb)

        floors = branch.floors if (branch and branch.floors) else []

        floors_cap_autos = sum(f.capacidad_total or 0 for f in floors)
        floors_occ_autos = sum(f.ocupacion_actual or 0 for f in floors)
        floors_cap_motos = sum(f.capacidad_motos or 0 for f in floors)
        floors_occ_motos = sum(f.ocupacion_motos or 0 for f in floors)
        floors_cap_camionetas = sum((getattr(f, 'capacidad_camionetas', 5) or 0) for f in floors)
        floors_occ_camionetas = sum((getattr(f, 'ocupacion_camionetas', 0) or 0) for f in floors)
        floors_cap_res_autos = sum((getattr(f, 'capacidad_reservas_autos', 0) or 0) for f in floors)
        floors_occ_res_autos = sum((getattr(f, 'ocupacion_reservas_autos', 0) or 0) for f in floors)
        floors_cap_res_motos = sum((getattr(f, 'capacidad_reservas_motos', 0) or 0) for f in floors)
        floors_occ_res_motos = sum((getattr(f, 'ocupacion_reservas_motos', 0) or 0) for f in floors)
        floors_cap_res_camionetas = sum((getattr(f, 'capacidad_reservas_camionetas', 0) or 0) for f in floors)
        floors_occ_res_camionetas = sum((getattr(f, 'ocupacion_reservas_camionetas', 0) or 0) for f in floors)
        floors_cap_reservas = sum((getattr(f, 'capacidad_reservas', 0) or 0) for f in floors)

        cap_total = cap_autos_pb + floors_cap_autos
        occ_total = occ_autos_pb + floors_occ_autos
        cap_motos = cap_motos_pb + floors_cap_motos
        occ_motos = occ_motos_pb + floors_occ_motos
        cap_camionetas = cap_camionetas_pb + floors_cap_camionetas
        occ_camionetas = occ_camionetas_pb + floors_occ_camionetas

        cap_res_autos = cap_res_autos_pb + floors_cap_res_autos
        occ_res_autos = occ_res_autos_pb + floors_occ_res_autos
        cap_res_motos = cap_res_motos_pb + floors_cap_res_motos
        occ_res_motos = occ_res_motos_pb + floors_occ_res_motos
        cap_res_camionetas = cap_res_camionetas_pb + floors_cap_res_camionetas
        occ_res_camionetas = occ_res_camionetas_pb + floors_occ_res_camionetas
        cap_reservas = cap_reservas_pb + floors_cap_reservas
        ocupadas_reservadas = OccupancyService.ocupacion_reservas_vigentes(db, branch.nombre)
        occ_res_autos = max(occ_res_autos, ocupadas_reservadas["autos"])
        occ_res_motos = max(occ_res_motos, ocupadas_reservadas["motos"])
        occ_res_camionetas = max(occ_res_camionetas, ocupadas_reservadas["camionetas"])
        occ_reservas = occ_res_autos + occ_res_motos + occ_res_camionetas

        return {
            "capacidad_total": cap_total,
            "ocupacion_actual": occ_total,
            "capacidad_motos": cap_motos,
            "ocupacion_motos": occ_motos,
            "capacidad_camionetas": cap_camionetas,
            "ocupacion_camionetas": occ_camionetas,
            "capacidad_reservas": cap_reservas,
            "ocupacion_reservas": occ_reservas,
            "capacidad_reservas_autos": cap_res_autos,
            "ocupacion_reservas_autos": occ_res_autos,
            "capacidad_reservas_motos": cap_res_motos,
            "ocupacion_reservas_motos": occ_res_motos,
            "capacidad_reservas_camionetas": cap_res_camionetas,
            "ocupacion_reservas_camionetas": occ_res_camionetas,
            "disponibilidad": max(0, cap_total - occ_total),
            "disponibilidad_motos": max(0, cap_motos - occ_motos),
            "disponibilidad_camionetas": max(0, cap_camionetas - occ_camionetas),
            "disponibilidad_reservas": max(0, cap_reservas - occ_reservas),
            "disponibilidad_reservas_autos": max(0, cap_res_autos - occ_res_autos),
            "disponibilidad_reservas_motos": max(0, cap_res_motos - occ_res_motos),
            "disponibilidad_reservas_camionetas": max(0, cap_res_camionetas - occ_res_camionetas),
        }

    @staticmethod
    def current_occupancy(db: Session, sucursal: str, organization_id=None) -> list:
        """Lista vehículos estacionados en la sede (o todas si admin global) con deuda calculada.
        Optimizado para unicidad y orden (una sola query por patente vía subconsulta).
        Con `organization_id` y sin `sucursal`, acota a las sedes de esa empresa."""
        # 1. ENTRADAS MAS RECIENTES POR PATENTE EN LA SEDE (ID MAXIMO DE ENTRADA POR PATENTE)
        entradas = AccessRepository.get_current_entries(db, sucursal=sucursal, organization_id=organization_id)

        # 3. SALIDAS POSTERIORES POR (PATENTE, SUCURSAL): 1 SOLA QUERY AGRUPADA
        salida_max = {}
        if entradas:
            patentes = {e.patente_detectada for e in entradas}
            sucursales = {e.sucursal for e in entradas if e.sucursal}
            salida_max = AccessRepository.get_exit_max_by_patente_sucursal(
                db, list(patentes), list(sucursales)
            )

        # 4. RESERVAS DE LAS ENTRADAS: 1 SOLA QUERY
        reservas = {}
        res_ids = [e.reserva_id for e in entradas if e.reserva_id]
        if res_ids:
            reservas = {
                r.id: r for r in ReservationRepository.get_by_ids(db, res_ids)
            }

        # 5. TARIFAS HORARIAS PRECARGADAS (EVITA 1 QUERY A SETTINGS POR VEHICULO)
        RATE_CLAVES = {
            "Auto": ("precio_30min", "precio_hora"),
            "Moto": ("precio_30min_moto", "precio_hora_moto"),
            "Camioneta": ("precio_30min_camioneta", "precio_hora_camioneta")
        }
        sucursales = {e.sucursal for e in entradas if e.sucursal}
        todas_claves = [c for pair in RATE_CLAVES.values() for c in pair]
        rate_map = {
            (r.clave, r.sucursal): r.valor
            for r in SettingsRepository.get_rates_by_claves(db, todas_claves, sucursales)
        }

        def calc_debt(entry_time_str, suc, tipo):
            clave30, clave_hora = RATE_CLAVES.get(tipo, ("precio_30min", "precio_hora"))
            fraccion = rate_map.get((clave30, suc))
            hora = rate_map.get((clave_hora, suc))
            delta = TimeService.now() - parse_fecha(entry_time_str)
            return BillingService.hourly_amount_from_rates(delta.total_seconds() / 3600, hora, fraccion)

        res = []
        for e in entradas:
            # 6. EXCLUIR ENTRADAS QUE YA TIENEN SALIDA POSTERIOR
            if salida_max.get((e.patente_detectada, e.sucursal), 0) > e.id:
                continue

            floor_name = e.floor.nombre if e.floor else None

            deuda = MONEY_ZERO
            ya_pago = e.pago_confirmado
            reserva_info = None
            en_cortesia = False

            if e.reserva_id:
                r = reservas.get(e.reserva_id)
                if r:
                    pagada = r.estado_pago == PaymentStatus.PAGADO
                    reserva_info = {"id": r.id, "tipo_estadia": r.tipo_estadia, "estado_pago": r.estado_pago}
                    now_str = TimeService.now_str()
                    # SI LA RESERVA EXPIRÓ (COMPLETADA/CANCELADA O FECHA_FIN YA PASÓ), ACUMULAR DEUDA DESDE ESE MOMENTO
                    if r.estado_reserva in [ReservationStatus.COMPLETADA, ReservationStatus.CANCELADA] or r.fecha_fin < now_str:
                        extra = calc_debt(r.fecha_fin, e.sucursal, e.tipo_vehiculo) or MONEY_ZERO
                        if pagada:
                            deuda = max(0, extra - (e.costo_estadia or 0))
                            ya_pago = deuda == 0
                        else:
                            # NUNCA ABONÓ LA RESERVA: ADEUDA EL MONTO DE LA RESERVA + EL TIEMPO EXTRA ACUMULADO
                            deuda = (r.monto_total or 0) + max(0, extra - (e.costo_estadia or 0))
                            ya_pago = deuda == 0
                    else:
                        # RESERVA VIGENTE DENTRO DE SU RANGO HORARIO
                        if pagada:
                            deuda = MONEY_ZERO
                            ya_pago = True
                        else:
                            # INGRESÓ CON RESERVA SIN PAGAR: DEBE EL MONTO DE LA RESERVA
                            deuda = (r.monto_total or 0)
                            ya_pago = deuda == 0
            elif not e.pago_confirmado:
                entrada_dt = parse_fecha(e.fecha_hora)
                minutos_transcurridos = (TimeService.now() - entrada_dt).total_seconds() / 60
                if minutos_transcurridos <= 10:
                    # CORTESIA: PRIMEROS 10 MINUTOS GRATIS
                    en_cortesia = True
                else:
                    deuda = calc_debt(e.fecha_hora, e.sucursal, e.tipo_vehiculo)

            res.append({
                "patente": e.patente_detectada,
                "tipo_vehiculo": e.tipo_vehiculo,
                "ingreso": e.fecha_hora,
                "deuda": deuda,
                "ya_pago": ya_pago,
                "en_cortesia": en_cortesia,
                "es_reserva": e.reserva_id is not None,
                "reserva": reserva_info,
                "sucursal": e.sucursal,
                "floor_nombre": floor_name
            })
        return res