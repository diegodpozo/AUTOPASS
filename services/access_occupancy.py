"""Ocupación física de plazas: incremento/decremento de ocupación (aforo PB y pisos)
y de plazas de reserva, usados por todos los flujos de acceso (ALPR, QR y manuales)."""


class AccessOccupancyMixin:

    @staticmethod
    def _tipo_lower(tipo_vehiculo) -> str:
        """Normaliza un tipo de vehículo (enum o str) a minúsculas."""
        tipo_str = tipo_vehiculo.value if hasattr(tipo_vehiculo, 'value') else str(tipo_vehiculo or "Auto")
        return tipo_str.lower()

    @staticmethod
    def _inc_reserva_occ(target_obj, tipo_vehiculo):
        """Incrementa plazas de reserva (general y por tipo) sobre aforo/piso."""
        tipo_lower = AccessOccupancyMixin._tipo_lower(tipo_vehiculo)
        target_obj.ocupacion_reservas = (getattr(target_obj, 'ocupacion_reservas', 0) or 0) + 1
        if "moto" in tipo_lower:
            target_obj.ocupacion_reservas_motos = (getattr(target_obj, 'ocupacion_reservas_motos', 0) or 0) + 1
        elif "camioneta" in tipo_lower:
            target_obj.ocupacion_reservas_camionetas = (getattr(target_obj, 'ocupacion_reservas_camionetas', 0) or 0) + 1
        else:
            target_obj.ocupacion_reservas_autos = (getattr(target_obj, 'ocupacion_reservas_autos', 0) or 0) + 1

    @staticmethod
    def _dec_reserva_occ(target_obj, tipo_vehiculo):
        """Decrementa plazas de reserva (general y por tipo) sin dejar valores negativos."""
        tipo_lower = AccessOccupancyMixin._tipo_lower(tipo_vehiculo)
        if (getattr(target_obj, 'ocupacion_reservas', 0) or 0) > 0:
            target_obj.ocupacion_reservas -= 1
        if "moto" in tipo_lower:
            if (getattr(target_obj, 'ocupacion_reservas_motos', 0) or 0) > 0:
                target_obj.ocupacion_reservas_motos -= 1
        elif "camioneta" in tipo_lower:
            if (getattr(target_obj, 'ocupacion_reservas_camionetas', 0) or 0) > 0:
                target_obj.ocupacion_reservas_camionetas -= 1
        else:
            if (getattr(target_obj, 'ocupacion_reservas_autos', 0) or 0) > 0:
                target_obj.ocupacion_reservas_autos -= 1

    @classmethod
    def _asignar_plaza(cls, target_obj, tipo_vehiculo, es_reserva: bool):
        """Suma una plaza al aforo/piso: plazas de reserva si `es_reserva`, si no ocupación física según tipo."""
        if es_reserva:
            cls._inc_reserva_occ(target_obj, tipo_vehiculo)
            return
        tipo_lower = cls._tipo_lower(tipo_vehiculo)
        if "moto" in tipo_lower:
            target_obj.ocupacion_motos = (getattr(target_obj, 'ocupacion_motos', 0) or 0) + 1
        elif "camioneta" in tipo_lower:
            target_obj.ocupacion_camionetas = (getattr(target_obj, 'ocupacion_camionetas', 0) or 0) + 1
        else:
            target_obj.ocupacion_actual = (getattr(target_obj, 'ocupacion_actual', 0) or 0) + 1

    @classmethod
    def _liberar_plaza(cls, target_obj, tipo_vehiculo, es_reserva: bool):
        """Quita una plaza del aforo/piso: plazas de reserva si `es_reserva`, si no ocupación física anti-negativa."""
        if es_reserva:
            cls._dec_reserva_occ(target_obj, tipo_vehiculo)
            return
        tipo_lower = cls._tipo_lower(tipo_vehiculo)
        if "moto" in tipo_lower:
            if (getattr(target_obj, 'ocupacion_motos', 0) or 0) > 0:
                target_obj.ocupacion_motos -= 1
        elif "camioneta" in tipo_lower:
            if (getattr(target_obj, 'ocupacion_camionetas', 0) or 0) > 0:
                target_obj.ocupacion_camionetas -= 1
        else:
            if (getattr(target_obj, 'ocupacion_actual', 0) or 0) > 0:
                target_obj.ocupacion_actual -= 1

    @staticmethod
    def _capacidad_por_tipo(aforo, tipo_vehiculo):
        """(capacidad, ocupacion) según tipo de vehículo para validar el aforo."""
        tipo_lower = AccessOccupancyMixin._tipo_lower(tipo_vehiculo)
        if "moto" in tipo_lower:
            return aforo.capacidad_motos, aforo.ocupacion_motos
        if "camioneta" in tipo_lower:
            return getattr(aforo, 'capacidad_camionetas', 5), getattr(aforo, 'ocupacion_camionetas', 0)
        return aforo.capacidad_total, aforo.ocupacion_actual