"""Ocupación física de plazas: incremento/decremento de ocupación (aforo PB y pisos)
y de plazas de reserva, usados por todos los flujos de acceso (ALPR, QR y manuales)."""


class AccessOccupancyMixin:						# Define la clase `AccessOccupancyMixin`, mixin que
									# aporta logica de ocupacion a los servicios de
									# acceso

    @staticmethod							# Decorador `@staticmethod` que marca `_tipo_lower`
									# como metodo estatico
    def _tipo_lower(tipo_vehiculo) -> str:				# Define `_tipo_lower(tipo_vehiculo)`: normaliza un
									# tipo de vehiculo (enum o str) a minusculas
        """Normaliza un tipo de vehículo (enum o str) a minúsculas."""
        tipo_str = tipo_vehiculo.value if hasattr(tipo_vehiculo, 'value') else str(tipo_vehiculo or "Auto")
									# Obtiene el valor del enum o convierte a str, con
									# 'Auto' por defecto si viene vacio
        return tipo_str.lower()						# Devuelve el tipo normalizado en minusculas

    @staticmethod							# Decorador `@staticmethod` que marca
									# `_inc_reserva_occ` como metodo estatico
    def _inc_reserva_occ(target_obj, tipo_vehiculo):			# Define `_inc_reserva_occ(target_obj,
									# tipo_vehiculo)`: incrementa plazas de reserva
        """Incrementa plazas de reserva (general y por tipo) sobre aforo/piso."""
        tipo_lower = AccessOccupancyMixin._tipo_lower(tipo_vehiculo)	# Normaliza el tipo de vehiculo a minusculas para
									# comparar
        target_obj.ocupacion_reservas = (getattr(target_obj, 'ocupacion_reservas', 0) or 0) + 1
									# Incrementa el contador general
									# `ocupacion_reservas` en 1 (tratando None como 0)
        if "moto" in tipo_lower:					# Si el tipo contiene 'moto', incrementa
									# `ocupacion_reservas_motos`
            target_obj.ocupacion_reservas_motos = (getattr(target_obj, 'ocupacion_reservas_motos', 0) or 0) + 1
									# Suma 1 al contador `ocupacion_reservas_motos`
        elif "camioneta" in tipo_lower:					# Rama `elif`: si el tipo contiene 'camioneta',
									# incrementa `ocupacion_reservas_camionetas`
            target_obj.ocupacion_reservas_camionetas = (getattr(target_obj, 'ocupacion_reservas_camionetas', 0) or 0) + 1
									# Incrementa el contador de reservas de camionetas
        else:								# Rama `else`: cualquier otro tipo se trata como
									# auto
            target_obj.ocupacion_reservas_autos = (getattr(target_obj, 'ocupacion_reservas_autos', 0) or 0) + 1
									# Incrementa `ocupacion_reservas_autos`, el
									# contador de reservas de autos

    @staticmethod							# Decorador `@staticmethod` que marca
									# `_dec_reserva_occ` como metodo estatico
    def _dec_reserva_occ(target_obj, tipo_vehiculo):			# Define `_dec_reserva_occ(target_obj,
									# tipo_vehiculo)`: decrementa plazas de reserva
        """Decrementa plazas de reserva (general y por tipo) sin dejar valores negativos."""
        tipo_lower = AccessOccupancyMixin._tipo_lower(tipo_vehiculo)	# Normaliza el tipo de vehiculo a minusculas
        if (getattr(target_obj, 'ocupacion_reservas', 0) or 0) > 0:	# Comprueba que el contador general de reservas sea
									# mayor a 0 antes de decrementar
            target_obj.ocupacion_reservas -= 1				# Decrementa `ocupacion_reservas` en 1, evitando
									# negativos
        if "moto" in tipo_lower:					# Si el tipo contiene 'moto', evalua decrementar el
									# contador de reservas de motos
            if (getattr(target_obj, 'ocupacion_reservas_motos', 0) or 0) > 0:
									# Comprueba que haya reservas de motos antes de
									# decrementar, evitando negativos
                target_obj.ocupacion_reservas_motos -= 1		# Decrementa `ocupacion_reservas_motos` en 1
        elif "camioneta" in tipo_lower:					# Rama `elif` para camionetas
            if (getattr(target_obj, 'ocupacion_reservas_camionetas', 0) or 0) > 0:
									# Comprueba que haya reservas de camionetas antes
									# de decrementar
                target_obj.ocupacion_reservas_camionetas -= 1		# Decrementa `ocupacion_reservas_camionetas` en 1
        else:								# Rama `else` para autos
            if (getattr(target_obj, 'ocupacion_reservas_autos', 0) or 0) > 0:
									# Comprueba que haya reservas de autos antes de
									# decrementar
                target_obj.ocupacion_reservas_autos -= 1		# Decrementa `ocupacion_reservas_autos` en 1

    @classmethod							# Decorador `@classmethod` porque el metodo usa la
									# clase para invocar otros helpers
    def _asignar_plaza(cls, target_obj, tipo_vehiculo, es_reserva: bool):
									# Define `_asignar_plaza(target_obj, tipo_vehiculo,
									# es_reserva)`: suma una plaza
        """Suma una plaza al aforo/piso: plazas de reserva si `es_reserva`, si no ocupación física según tipo."""
        if es_reserva:							# Si se trata de una plaza de reserva, delega en el
									# incremento de reservas
            cls._inc_reserva_occ(target_obj, tipo_vehiculo)		# Incrementa la ocupacion de reserva
									# correspondiente al tipo de vehiculo
            return							# Termina el caso de reserva sin tocar la ocupacion
									# fisica
        tipo_lower = cls._tipo_lower(tipo_vehiculo)			# Normaliza el tipo de vehiculo a minusculas
        if "moto" in tipo_lower:					# Si el tipo contiene 'moto', incrementa la
									# ocupacion fisica de motos
            target_obj.ocupacion_motos = (getattr(target_obj, 'ocupacion_motos', 0) or 0) + 1
									# Incrementa `ocupacion_motos` en 1 (tratando None
									# como 0)
        elif "camioneta" in tipo_lower:					# Rama `elif` para camionetas
            target_obj.ocupacion_camionetas = (getattr(target_obj, 'ocupacion_camionetas', 0) or 0) + 1
									# Incrementa `ocupacion_camionetas` en 1
        else:								# Rama `else` para autos
            target_obj.ocupacion_actual = (getattr(target_obj, 'ocupacion_actual', 0) or 0) + 1
									# Incrementa `ocupacion_actual` (autos) en 1

    @classmethod							# Decorador `@classmethod` porque `_liberar_plaza`
									# usa la clase para llamar a otros helpers
    def _liberar_plaza(cls, target_obj, tipo_vehiculo, es_reserva: bool):
									# Define `_liberar_plaza(target_obj, tipo_vehiculo,
									# es_reserva)`: quita una plaza
        """Quita una plaza del aforo/piso: plazas de reserva si `es_reserva`, si no ocupación física anti-negativa."""
        if es_reserva:							# Si es una plaza de reserva, delega en el
									# decremento de reservas
            cls._dec_reserva_occ(target_obj, tipo_vehiculo)		# Decrementa la ocupacion de reserva del tipo
									# correspondiente
            return							# Termina el caso de reserva sin tocar la ocupacion
									# fisica
        tipo_lower = cls._tipo_lower(tipo_vehiculo)			# Normaliza el tipo de vehiculo a minusculas
        if "moto" in tipo_lower:					# Si el tipo contiene 'moto', prepara el decremento
									# de motos
            if (getattr(target_obj, 'ocupacion_motos', 0) or 0) > 0:	# Comprueba que haya ocupacion de motos antes de
									# decrementar, evitando negativos
                target_obj.ocupacion_motos -= 1				# Decrementa `ocupacion_motos` en 1
        elif "camioneta" in tipo_lower:					# Rama `elif` para camionetas
            if (getattr(target_obj, 'ocupacion_camionetas', 0) or 0) > 0:
									# Comprueba que haya ocupacion de camionetas antes
									# de decrementar
                target_obj.ocupacion_camionetas -= 1			# Decrementa `ocupacion_camionetas` en 1
        else:								# Rama `else` para autos
            if (getattr(target_obj, 'ocupacion_actual', 0) or 0) > 0:	# Comprueba que haya ocupacion de autos antes de
									# decrementar
                target_obj.ocupacion_actual -= 1			# Decrementa `ocupacion_actual` (autos) en 1

    @staticmethod							# Decorador `@staticmethod` que marca
									# `_capacidad_por_tipo` como metodo estatico
    def _capacidad_por_tipo(aforo, tipo_vehiculo):			# Define `_capacidad_por_tipo(aforo,
									# tipo_vehiculo)`: devuelve capacidad y ocupacion
									# segun tipo
        """(capacidad, ocupacion) según tipo de vehículo para validar el aforo."""
        tipo_lower = AccessOccupancyMixin._tipo_lower(tipo_vehiculo)	# Normaliza el tipo de vehiculo a minusculas
        if "moto" in tipo_lower:					# Si el tipo contiene 'moto', devuelve la capacidad
									# y ocupacion de motos
            return aforo.capacidad_motos, aforo.ocupacion_motos		# Devuelve `capacidad_motos` y `ocupacion_motos`
									# del aforo
        if "camioneta" in tipo_lower:					# Si el tipo contiene 'camioneta', devuelve su
									# capacidad y ocupacion con valores por defecto
            return getattr(aforo, 'capacidad_camionetas', 5), getattr(aforo, 'ocupacion_camionetas', 0)
									# Devuelve la capacidad/ocupacion de camionetas
									# usando `getattr` por si la columna no existe
        return aforo.capacidad_total, aforo.ocupacion_actual		# Caso por defecto (autos): devuelve
									# `capacidad_total` y `ocupacion_actual`