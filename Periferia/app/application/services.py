"""
application/services.py - Servicios de lógica de negocio y procesamiento
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

from domain.models import (
    Signal, RuleType, VehicleType, ActionType,
    EARTH_RADIUS_KM
)
import math

logger = logging.getLogger(__name__)


class RuleService:
    """Servicio para evaluación de reglas complejas."""
    
    @staticmethod
    async def evaluate_complex_rules(signal: Signal, signal_id: int, reglas: List[Dict], 
                                     geofence_cache: Dict, schedule_cache: Dict,
                                     pool, redis_enabled: bool, metrics: Dict) -> List[Tuple]:
        """Evalúa reglas complejas incluyendo geocercas y horarios."""
        alerts_to_insert = []
        
        for regla in reglas:
            violation = False
            mensaje = ""
            rule_type = regla["rule_type"]
            
            # VELOCIDAD MÁXIMA
            if rule_type == RuleType.MAX_SPEED:
                limite = float(regla["comparison_value"])
                if signal.speed > limite:
                    violation = True
                    mensaje = f"Exceso velocidad: {signal.speed:.1f} > {limite} km/h"
            
            # BOTÓN DE PÁNICO
            elif rule_type == RuleType.PANIC_BUTTON and signal.panic_button:
                violation = True
                mensaje = "🚨 BOTÓN DE PÁNICO ACTIVADO"
            
            # TEMPERATURA ALTA (camiones refrigerados)
            elif rule_type == RuleType.MAX_TEMP and signal.temperature is not None:
                if signal.vehicle_type == VehicleType.TRUCK:
                    limite = float(regla["comparison_value"])
                    if signal.temperature > limite:
                        violation = True
                        mensaje = f"Temperatura ALTA: {signal.temperature:.1f}°C > {limite}°C"
            
            # TEMPERATURA BAJA (camiones refrigerados)
            elif rule_type == RuleType.MIN_TEMP and signal.temperature is not None:
                if signal.vehicle_type == VehicleType.TRUCK:
                    limite = float(regla["comparison_value"])
                    if signal.temperature < limite:
                        violation = True
                        mensaje = f"Temperatura BAJA: {signal.temperature:.1f}°C < {limite}°C"
            
            # GEOFENCE EXIT (Salida de zona permitida)
            elif rule_type == RuleType.GEOFENCE_EXIT:
                if signal.vehicle_id in geofence_cache:
                    geofences = geofence_cache[signal.vehicle_id]
                    if await RuleService._check_geofence_violation(signal, geofences, regla["comparison_value"]):
                        violation = True
                        mensaje = f"Salida de zona: {regla['comparison_value']}"
            
            # SCHEDULE (Horario no permitido)
            elif rule_type == RuleType.SCHEDULE:
                if signal.vehicle_id in schedule_cache:
                    schedule = schedule_cache[signal.vehicle_id]
                    if await RuleService._check_schedule_violation(signal, schedule):
                        violation = True
                        mensaje = f"Movimiento en horario no permitido: {schedule.get('start_time')}-{schedule.get('end_time')}"
            
            # UNPLANNED STOP (Detención no planeada)
            elif rule_type == RuleType.UNPLANNED_STOP:
                if await RuleService._check_unplanned_stop(signal, pool):
                    violation = True
                    mensaje = "Detención no planeada detectada"
            
            # DOOR SENSOR (Puerta abierta en movimiento)
            elif rule_type == RuleType.DOOR_SENSOR:
                if signal.metadata.get('door_status') == 'open' and signal.speed > 1.0:
                    violation = True
                    mensaje = "Puerta abierta durante movimiento"
            
            # PROCESAR VIOLACIÓN
            if violation:
                logger.warning(f"🛑 ALERTA [{rule_type}]: {mensaje}")
                alerts_to_insert.append((
                    signal.vehicle_id, 
                    regla["id"],
                    signal_id,
                    mensaje, 
                    regla["action_type"],
                    datetime.utcnow()
                ))
                
                # ENVIAR NOTIFICACIÓN
                await NotificationService.send_notification(signal.vehicle_id, mensaje, regla["action_type"], pool)
        
        # Actualizar métricas
        if alerts_to_insert:
            metrics["alerts_generated"] = metrics.get("alerts_generated", 0) + len(alerts_to_insert)
        
        return alerts_to_insert
    
    @staticmethod
    async def evaluate_emergency_rules(signal: Signal, signal_id: int, reglas: List[Dict],
                                       pool, metrics: Dict):
        """Evalúa solo reglas de emergencia (más rápido)."""
        for regla in reglas:
            if regla["rule_type"] == RuleType.PANIC_BUTTON and signal.panic_button:
                mensaje = "🚨 EMERGENCIA: Botón de pánico activado"
                logger.critical(mensaje)
                
                try:
                    async with pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO alerts (vehicle_id, rule_id, signal_id, message, action_taken, timestamp)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """, signal.vehicle_id, regla["id"], signal_id, mensaje, regla["action_type"], datetime.utcnow())
                        
                        metrics["alerts_generated"] = metrics.get("alerts_generated", 0) + 1
                        
                    # Notificación inmediata
                    await NotificationService.send_emergency_notification(signal.vehicle_id, mensaje, pool)
                    
                except Exception as e:
                    logger.error(f"❌ Error en emergencia: {e}")
    
    @staticmethod
    async def _check_geofence_violation(signal: Signal, geofences: List, zone_name: str) -> bool:
        """Verifica si el vehículo salió de una geocerca."""
        try:
            for geofence in geofences:
                if geofence.get('name') == zone_name and geofence.get('is_allowed', True):
                    center = geofence.get('center', {})
                    radius_km = geofence.get('radius_km', 0)
                    
                    # Calcular distancia al centro
                    distance = RuleService._calculate_distance(
                        signal.latitude, signal.longitude,
                        center.get('latitude', 0), center.get('longitude', 0)
                    )
                    
                    # Si está fuera del radio permitido
                    if distance > radius_km:
                        return True
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando geocerca: {e}")
            return False
    
    @staticmethod
    async def _check_schedule_violation(signal: Signal, schedule: Dict) -> bool:
        """Verifica si el vehículo se mueve fuera del horario permitido."""
        try:
            from datetime import time
            signal_time = signal.timestamp.time()
            
            # Convertir strings a time objects
            start_str = schedule.get('start_time', '00:00')
            end_str = schedule.get('end_time', '23:59')
            
            start_time = time.fromisoformat(start_str)
            end_time = time.fromisoformat(end_str)
            
            # Verificar día de la semana
            day_of_week = signal.timestamp.isoweekday()  # 1=Lunes, 7=Domingo
            allowed_days = schedule.get('days_of_week', [1, 2, 3, 4, 5, 6, 7])
            
            if day_of_week not in allowed_days:
                return True  # Violación: día no permitido
            
            # Verificar horario
            if start_time <= end_time:
                # Horario normal (ej: 06:00-22:00)
                if not (start_time <= signal_time <= end_time):
                    return True  # Violación: fuera de horario
            else:
                # Horario que cruza medianoche (ej: 22:00-06:00)
                if not (signal_time >= start_time or signal_time <= end_time):
                    return True  # Violación: fuera de horario
            
            return False
        except Exception as e:
            logger.error(f"❌ Error verificando horario: {e}")
            return False
    
    @staticmethod
    async def _check_unplanned_stop(signal: Signal, pool) -> bool:
        """Detecta detenciones no planeadas."""
        try:
            # Obtener últimas señales del vehículo
            async with pool.acquire() as conn:
                recent_signals = await conn.fetch("""
                    SELECT speed, timestamp 
                    FROM signals 
                    WHERE vehicle_id = $1 
                    AND timestamp > NOW() - INTERVAL '5 minutes'
                    ORDER BY timestamp DESC
                    LIMIT 10
                """, signal.vehicle_id)
                
                if len(recent_signals) >= 3:
                    # Verificar si las últimas 3 señales muestran velocidad cero
                    last_three = recent_signals[:3]
                    all_stopped = all(s['speed'] < 1.0 for s in last_three)
                    
                    # Verificar que no estaba detenido antes (primeras señales más antiguas)
                    if len(recent_signals) >= 5:
                        older_signals = recent_signals[3:5]
                        was_moving = any(s['speed'] > 5.0 for s in older_signals)
                        
                        if all_stopped and was_moving:
                            return True  # Detención no planeada detectada
            
            return False
        except Exception as e:
            logger.error(f"❌ Error detectando detención: {e}")
            return False
    
    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distancia en km usando fórmula de Haversine."""
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return EARTH_RADIUS_KM * c


class NotificationService:
    """Servicio para envío de notificaciones."""
    
    @staticmethod
    async def send_notification(vehicle_id: str, mensaje: str, accion: str, pool):
        """Envía notificación al propietario."""
        try:
            async with pool.acquire() as conn:
                # Obtener propietario
                owner = await conn.fetchrow("""
                    SELECT o.id, o.full_name, o.email, o.phone
                    FROM owners o
                    JOIN vehicles v ON v.owner_id = o.id
                    WHERE v.id = $1
                """, vehicle_id)
                
                if owner:
                    # Determinar canal según acción
                    if accion in [ActionType.NOTIFY_POLICE.value, ActionType.CALL_EMERGENCY.value]:
                        channel = "emergency_services"
                        logger.critical(f"🚨 CONTACTANDO AUTORIDADES: {mensaje}")
                    elif accion == ActionType.NOTIFY_OWNER.value:
                        channel = "owner_sms"
                        logger.info(f"📱 SMS a {owner['phone']}: {mensaje}")
                    elif accion == ActionType.SMS_OWNER.value:
                        channel = "owner_sms"
                        logger.info(f"📱 SMS a {owner['phone']}: {mensaje}")
                    else:
                        channel = "log_only"
                    
                    # Registrar notificación
                    await conn.execute("""
                        INSERT INTO notifications (vehicle_id, owner_id, message, channel, status)
                        VALUES ($1, $2, $3, $4, 'sent')
                    """, vehicle_id, owner['id'], mensaje, channel)
                    
                    # Demo en consola
                    print(f"\n{'='*60}")
                    print(f"📨 NOTIFICACIÓN [{channel.upper()}]")
                    print(f"👤 Propietario: {owner['full_name']}")
                    print(f"🚗 Vehículo: {vehicle_id}")
                    print(f"📝 Mensaje: {mensaje}")
                    print(f"⏰ Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"{'='*60}\n")
                    
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
    
    @staticmethod
    async def send_emergency_notification(vehicle_id: str, mensaje: str, pool):
        """Envía notificación de emergencia (más rápido)."""
        try:
            async with pool.acquire() as conn:
                owner = await conn.fetchrow("""
                    SELECT o.phone FROM owners o
                    JOIN vehicles v ON v.owner_id = o.id
                    WHERE v.id = $1
                """, vehicle_id)
                
                if owner:
                    logger.critical(f"🚨 EMERGENCIA - Contactando a {owner['phone']}: {mensaje}")
                    
        except Exception as e:
            logger.error(f"❌ Error en notificación de emergencia: {e}")


class DataService:
    """Servicio para operaciones de base de datos."""
    
    @staticmethod
    async def persist_signal(signal: Signal, pool, api_instance_id: str) -> int:
        """Guarda señal en PostgreSQL."""
        metadata = {
            **signal.metadata,
            "panic_button": signal.panic_button,
            "temperature": signal.temperature,
            "vehicle_type": signal.vehicle_type.value if signal.vehicle_type else None,
            "processed_at": datetime.utcnow().isoformat(),
            "api_instance": api_instance_id
        }
        
        async with pool.acquire() as conn:
            signal_id = await conn.fetchval("""
                INSERT INTO signals (vehicle_id, timestamp, latitude, longitude, speed, heading, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """,
                signal.vehicle_id,
                signal.timestamp,
                signal.latitude,
                signal.longitude,
                signal.speed,
                0.0,  # heading por defecto
                json.dumps(metadata, default=str)
            )
            return signal_id
    
    @staticmethod
    async def persist_emergency_signal(signal: Signal, pool) -> int:
        """Guarda señal de emergencia (más rápido, menos validaciones)."""
        async with pool.acquire() as conn:
            signal_id = await conn.fetchval("""
                INSERT INTO signals (vehicle_id, timestamp, latitude, longitude, speed, heading, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """,
                signal.vehicle_id,
                signal.timestamp,
                signal.latitude,
                signal.longitude,
                signal.speed,
                0.0,
                json.dumps({"emergency": True, "panic_button": True}, default=str)
            )
            return signal_id
    
    @staticmethod
    async def get_rules(vehicle_id: str, pool, redis, redis_enabled: bool) -> List[Dict]:
        """Obtiene todas las reglas activas para un vehículo."""
        cache_key = f"rules:{vehicle_id}"
        
        if redis_enabled and redis:
            try:
                cached = await asyncio.wait_for(redis.get(cache_key), timeout=0.5)
                if cached:
                    return json.loads(cached)
            except:
                pass
        
        query = """
            SELECT id, rule_type, comparison_value, action_type, priority 
            FROM rules 
            WHERE vehicle_id = $1 AND is_active = TRUE
            ORDER BY priority DESC
        """
        
        try:
            async with pool.acquire() as conn:
                rows = await asyncio.wait_for(conn.fetch(query, vehicle_id), timeout=1.0)
        except asyncio.TimeoutError:
            return []
        except Exception as e:
            logger.error(f"❌ Error obteniendo reglas: {e}")
            return []
        
        reglas = [dict(fila) for fila in rows]

        if reglas and redis_enabled and redis:
            try:
                await asyncio.wait_for(
                    redis.setex(cache_key, 300, json.dumps(reglas, default=str)),
                    timeout=0.3
                )
            except:
                pass
        
        return reglas
    
    @staticmethod
    async def get_emergency_rules(vehicle_id: str, pool, redis, redis_enabled: bool) -> List[Dict]:
        """Obtiene solo reglas de emergencia (PANIC_BUTTON)."""
        cache_key = f"emergency_rules:{vehicle_id}"
        
        if redis_enabled and redis:
            try:
                cached = await asyncio.wait_for(redis.get(cache_key), timeout=0.1)
                if cached:
                    return json.loads(cached)
            except:
                pass
        
        query = """
            SELECT id, rule_type, comparison_value, action_type 
            FROM rules 
            WHERE vehicle_id = $1 AND is_active = TRUE AND rule_type = 'PANIC_BUTTON'
        """
        
        try:
            async with pool.acquire() as conn:
                rows = await asyncio.wait_for(conn.fetch(query, vehicle_id), timeout=0.5)
        except asyncio.TimeoutError:
            return []
        
        reglas = [dict(fila) for fila in rows]

        if reglas and redis_enabled and redis:
            try:
                await asyncio.wait_for(
                    redis.setex(cache_key, 600, json.dumps(reglas, default=str)),
                    timeout=0.1
                )
            except:
                pass
        
        return reglas
    
    @staticmethod
    async def bulk_insert_alerts(alerts_to_insert: List[Tuple], pool):
        """Inserta múltiples alertas en una sola operación."""
        if alerts_to_insert:
            try:
                async with pool.acquire() as conn:
                    await conn.executemany("""
                        INSERT INTO alerts (vehicle_id, rule_id, signal_id, message, action_taken, timestamp)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, alerts_to_insert)
            except Exception as e:
                logger.error(f"❌ Error insertando alertas: {e}")