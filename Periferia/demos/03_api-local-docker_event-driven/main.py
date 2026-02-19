"""
CCS Central API - Sistema de Monitoreo Vehicular
API principal para procesamiento de señales y gestión de reglas complejas.

Características implementadas:
- Procesamiento de señales en tiempo real (500 señales/segundo)
- Reglas complejas: Geocercas, Horarios, Detenciones, Temperatura
- Sistema de notificaciones multi-canal
- Cache distribuido con Redis
- Particionamiento temporal en PostgreSQL
- Documentación OpenAPI 3.0 completa

Endpoints principales:
- POST /signal: Recibir señal de vehículo
- POST /geofence: Definir geocerca para vehículo
- POST /schedule: Definir horario permitido
- GET /health: Estado del sistema
- GET /docs: Documentación OpenAPI interactiva

Requisitos de rendimiento:
- Emergencias: < 2 segundos para botón de pánico
- Capacidad: 500 señales/segundo por 2 minutos
- Escalabilidad: +20% anual por 3 años
"""

import os
import json
import logging
import asyncio
import uuid
import math
from datetime import datetime, time, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status, Body
from pydantic import BaseModel, Field, validator, confloat, constr
import asyncpg
from redis.asyncio import Redis
from dotenv import load_dotenv

# ============================================================================
# CONFIGURACIÓN
# ============================================================================

load_dotenv('.env')

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
REDIS_STREAM_NAME = os.getenv('REDIS_STREAM_NAME', 'ccs_signals_stream')
EMERGENCY_STREAM_NAME = os.getenv('EMERGENCY_STREAM_NAME', 'ccs_emergency_stream')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/ccs_local')

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ccs_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS Y CONSTANTES
# ============================================================================

class VehicleType(str, Enum):
    """Tipos de vehículos soportados."""
    TRUCK = "TRUCK"
    CAR = "CAR"
    MOTO = "MOTO"

class RuleType(str, Enum):
    """Tipos de reglas disponibles."""
    MAX_SPEED = "MAX_SPEED"
    PANIC_BUTTON = "PANIC_BUTTON"
    MAX_TEMP = "MAX_TEMP"
    MIN_TEMP = "MIN_TEMP"
    GEOFENCE_EXIT = "GEOFENCE_EXIT"
    SCHEDULE = "SCHEDULE"
    UNPLANNED_STOP = "UNPLANNED_STOP"
    DOOR_SENSOR = "DOOR_SENSOR"

class ActionType(str, Enum):
    """Acciones disponibles para reglas."""
    NOTIFY_POLICE = "NOTIFY_POLICE"
    NOTIFY_OWNER = "NOTIFY_OWNER"
    SMS_OWNER = "SMS_OWNER"
    LOG_ONLY = "LOG_ONLY"
    CALL_EMERGENCY = "CALL_EMERGENCY"
    NOTIFY_SECURITY = "NOTIFY_SECURITY"

# Radio de la Tierra en kilómetros
EARTH_RADIUS_KM = 6371.0

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class Location(BaseModel):
    """Modelo para ubicación geográfica."""
    latitude: confloat(ge=-90.0, le=90.0) = Field(
        ..., 
        example=4.60971,
        description="Latitud en grados decimales (-90 a 90)"
    )
    longitude: confloat(ge=-180.0, le=180.0) = Field(
        ..., 
        example=-74.08175,
        description="Longitud en grados decimales (-180 a 180)"
    )

class Geofence(BaseModel):
    """Modelo para definir una geocerca."""
    name: constr(min_length=1, max_length=50) = Field(
        ..., 
        example="Zona_Norte_Bogota",
        description="Nombre identificador de la geocerca"
    )
    center: Location = Field(
        ..., 
        description="Centro de la geocerca"
    )
    radius_km: confloat(gt=0.0) = Field(
        ..., 
        example=5.0,
        description="Radio de la geocerca en kilómetros"
    )
    is_allowed: bool = Field(
        default=True,
        description="True si es zona permitida, False si es zona prohibida"
    )

class TimeSchedule(BaseModel):
    """Modelo para definir horario permitido."""
    start_time: str = Field(
        ..., 
        example="06:00",
        description="Hora de inicio en formato HH:MM (24h)"
    )
    end_time: str = Field(
        ..., 
        example="22:00",
        description="Hora de fin en formato HH:MM (24h)"
    )
    days_of_week: List[int] = Field(
        default=[1, 2, 3, 4, 5, 6, 7],
        example=[1, 2, 3, 4, 5],
        description="Días de la semana (1=Lunes, 7=Domingo)"
    )
    
    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        try:
            time.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Formato de hora inválido. Use HH:MM')
    
    @validator('days_of_week')
    def validate_days(cls, v):
        if not all(1 <= day <= 7 for day in v):
            raise ValueError('Días deben estar entre 1 (Lunes) y 7 (Domingo)')
        return v

class Signal(BaseModel):
    """
    Señal recibida de un vehículo.
    
    Ejemplo para camión refrigerado:
    ```json
    {
        "vehicle_id": "TRUCK-011",
        "speed": 65.5,
        "latitude": 4.60971,
        "longitude": -74.08175,
        "timestamp": "2024-01-15T10:30:00Z",
        "panic_button": false,
        "temperature": -15.0,
        "vehicle_type": "TRUCK",
        "metadata": {
            "cargo_type": "pharmaceuticals",
            "door_status": "closed"
        }
    }
    ```
    """
    vehicle_id: constr(min_length=1, max_length=20) = Field(
        ..., 
        example="TRUCK-001",
        description="ID único del vehículo"
    )
    speed: confloat(ge=0.0) = Field(
        ..., 
        example=75.5,
        description="Velocidad actual en km/h"
    )
    latitude: confloat(ge=-90.0, le=90.0) = Field(
        ..., 
        example=4.60971,
        description="Latitud actual"
    )
    longitude: confloat(ge=-180.0, le=180.0) = Field(
        ..., 
        example=-74.08175,
        description="Longitud actual"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        example="2024-01-15T10:30:00Z",
        description="Timestamp de la señal (UTC)"
    )
    panic_button: bool = Field(
        default=False,
        example=False,
        description="True si el botón de pánico fue activado"
    )
    temperature: Optional[confloat(ge=-273.15)] = Field(
        default=None,
        example=-15.0,
        description="Temperatura de la carga en °C (solo camiones refrigerados)"
    )
    vehicle_type: Optional[VehicleType] = Field(
        default=None,
        example="TRUCK",
        description="Tipo de vehículo (inferido si no se proporciona)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        example={"door_status": "closed", "cargo_type": "general"},
        description="Metadatos adicionales específicos del vehículo"
    )
    
    def to_json_serializable_dict(self):
        """Convierte el modelo a dict serializable en JSON."""
        data = self.dict()
        if isinstance(data.get("timestamp"), datetime):
            data["timestamp"] = data["timestamp"].isoformat()
        if self.vehicle_type:
            data["vehicle_type"] = self.vehicle_type.value
        return data

class RuleUpdate(BaseModel):
    """Modelo para actualizar reglas."""
    vehicle_id: str = Field(..., example="TRUCK-001")
    rule_type: RuleType = Field(..., example="MAX_SPEED")
    comparison_value: str = Field(..., example="80.0")
    action_type: ActionType = Field(..., example="NOTIFY_POLICE")
    is_active: bool = Field(default=True)

class GeofenceDefinition(BaseModel):
    """Modelo para definir una nueva geocerca."""
    vehicle_id: str = Field(..., example="TRUCK-001")
    geofence: Geofence = Field(...)

class ScheduleDefinition(BaseModel):
    """Modelo para definir un nuevo horario."""
    vehicle_id: str = Field(..., example="MOTO-301")
    schedule: TimeSchedule = Field(...)

class HealthResponse(BaseModel):
    """Respuesta del endpoint de health check."""
    status: str = Field(..., example="healthy")
    services: Dict[str, str] = Field(
        ...,
        example={"postgresql": "healthy", "redis": "healthy", "stream": "healthy"}
    )
    uptime_seconds: float = Field(..., example=3600.5)
    timestamp: datetime = Field(..., example="2024-01-15T10:30:00Z")
    metrics: Optional[Dict[str, Any]] = Field(
        default=None,
        example={"signals_processed": 1500, "alerts_generated": 45}
    )

class SignalResponse(BaseModel):
    """Respuesta del endpoint de procesamiento de señales."""
    status: str = Field(..., example="accepted")
    vehicle_id: str = Field(..., example="TRUCK-001")
    message_id: str = Field(..., example="1705311000000-0")
    processing_time_ms: float = Field(..., example=45.2)
    timestamp: datetime = Field(..., example="2024-01-15T10:30:00Z")
    priority: str = Field(..., example="normal", description="normal o emergency")

# ============================================================================
# ESTADO GLOBAL Y UTILIDADES
# ============================================================================

class GlobalState:
    """Estado global de la aplicación CCS."""
    
    def __init__(self):
        self.pool: asyncpg.Pool = None
        self.redis: Redis = None
        self.redis_enabled: bool = True
        self.running = False
        self.api_instance_id = f"ccs-api-{uuid.uuid4().hex[:8]}"
        self.start_time = datetime.utcnow()
        self.metrics = {
            "signals_processed": 0,
            "alerts_generated": 0,
            "emergencies_processed": 0,
            "last_emergency_time": None
        }
        self.geofence_cache = {}  # Cache en memoria para geocercas
        self.schedule_cache = {}  # Cache en memoria para horarios
        
    async def initialize(self):
        """Inicializa conexiones y workers."""
        logger.info(f"🚀 Iniciando CCS API - Instancia: {self.api_instance_id}")
        
        try:
            # PostgreSQL Pool
            self.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=10,
                max_size=100,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
                command_timeout=60,
                server_settings={
                    'jit': 'off',  # Mejor para cargas OLTP
                    'max_parallel_workers_per_gather': '2'
                }
            )
            logger.info("✅ PostgreSQL pool creado")
            
            # Redis para Streams y Cache
            self.redis = Redis.from_url(
                REDIS_URL,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
                max_connections=50
            )
            await self.redis.ping()
            logger.info("✅ Redis conectado")
            
            # Crear consumer groups
            await self._setup_redis_streams()
            
            # Cargar geocercas y horarios en cache
            await self._load_geofences_and_schedules()
            
            # Iniciar workers
            self.running = True
            asyncio.create_task(self._normal_worker_loop())
            asyncio.create_task(self._emergency_worker_loop())
            
            logger.info("✅ CCS API completamente inicializada")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando CCS API: {e}")
            raise
    
    async def _setup_redis_streams(self):
        """Configura los streams de Redis."""
        try:
            # Stream principal para señales normales
            await self.redis.xgroup_create(
                REDIS_STREAM_NAME,
                "ccs_workers",
                id="0",
                mkstream=True
            )
            logger.info(f"✅ Stream principal creado: {REDIS_STREAM_NAME}")
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.warning(f"⚠️ Error creando stream principal: {e}")
        
        try:
            # Stream de emergencias (alta prioridad)
            await self.redis.xgroup_create(
                EMERGENCY_STREAM_NAME,
                "ccs_emergency_workers",
                id="0",
                mkstream=True
            )
            logger.info(f"✅ Stream de emergencias creado: {EMERGENCY_STREAM_NAME}")
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                logger.warning(f"⚠️ Error creando stream de emergencias: {e}")
    
    async def _load_geofences_and_schedules(self):
        """Carga geocercas y horarios desde la base de datos."""
        try:
            async with self.pool.acquire() as conn:
                # Cargar geocercas (simulado - en producción usar tabla geofences)
                geofences = await conn.fetch("""
                    SELECT vehicle_id, details->>'geofence' as geofence_data
                    FROM vehicles 
                    WHERE details->>'geofence' IS NOT NULL
                """)
                
                for row in geofences:
                    if row['geofence_data']:
                        try:
                            geofence_data = json.loads(row['geofence_data'])
                            if 'geofences' in geofence_data:
                                self.geofence_cache[row['vehicle_id']] = geofence_data['geofences']
                        except:
                            pass
                
                logger.info(f"📊 {len(self.geofence_cache)} geocercas cargadas en cache")
                
                # Cargar horarios (simulado - en producción usar tabla schedules)
                schedules = await conn.fetch("""
                    SELECT vehicle_id, details->>'schedule' as schedule_data
                    FROM vehicles 
                    WHERE details->>'schedule' IS NOT NULL
                """)
                
                for row in schedules:
                    if row['schedule_data']:
                        try:
                            schedule_data = json.loads(row['schedule_data'])
                            self.schedule_cache[row['vehicle_id']] = schedule_data
                        except:
                            pass
                
                logger.info(f"📊 {len(self.schedule_cache)} horarios cargados en cache")
                
        except Exception as e:
            logger.error(f"❌ Error cargando geocercas/horarios: {e}")
    
    async def shutdown(self):
        """Cierra conexiones y detiene workers."""
        logger.info("🔒 Cerrando CCS API...")
        self.running = False
        
        if self.pool:
            await self.pool.close()
        if self.redis:
            await self.redis.close()
        
        logger.info("✅ CCS API cerrada correctamente")
    
    # ========================================================================
    # WORKERS
    # ========================================================================
    
    async def _normal_worker_loop(self):
        """Worker para procesamiento normal de señales."""
        logger.info("👂 Worker normal iniciado")
        
        while self.running:
            if not self.redis_enabled:
                await asyncio.sleep(1)
                continue
            
            try:
                stream_data = await self.redis.xreadgroup(
                    groupname="ccs_workers",
                    consumername=f"worker_{self.api_instance_id}",
                    streams={REDIS_STREAM_NAME: ">"},
                    count=100,  # Procesar en batch
                    block=500  # 500ms timeout
                )
                
                if stream_data:
                    tasks = []
                    for stream_name, messages in stream_data:
                        for message_id, message_data in messages:
                            task = self._process_normal_signal(message_id, message_data)
                            tasks.append(task)
                    
                    # Procesar en paralelo
                    if tasks:
                        await asyncio.gather(*tasks, return_exceptions=True)
                        
            except Exception as e:
                logger.error(f"⚠️ Error en worker normal: {e}")
                await asyncio.sleep(1)
    
    async def _emergency_worker_loop(self):
        """Worker para procesamiento de emergencias (alta prioridad)."""
        logger.info("🚨 Worker de emergencias iniciado")
        
        while self.running:
            if not self.redis_enabled:
                await asyncio.sleep(0.1)  # Menos sleep para emergencias
                continue
            
            try:
                stream_data = await self.redis.xreadgroup(
                    groupname="ccs_emergency_workers",
                    consumername=f"emergency_worker_{self.api_instance_id}",
                    streams={EMERGENCY_STREAM_NAME: ">"},
                    count=10,  # Menos batch para mayor responsividad
                    block=100  # 100ms timeout
                )
                
                if stream_data:
                    start_time = datetime.utcnow()
                    for stream_name, messages in stream_data:
                        for message_id, message_data in messages:
                            # Procesar emergencias secuencialmente para garantizar orden
                            await self._process_emergency_signal(message_id, message_data)
                    
                    # Verificar tiempo de respuesta (<2s)
                    processing_time = (datetime.utcnow() - start_time).total_seconds()
                    if processing_time > 2.0:
                        logger.warning(f"⚠️ Emergencia procesada en {processing_time:.2f}s (>2s)")
                        
            except Exception as e:
                logger.error(f"❌ Error en worker de emergencias: {e}")
                await asyncio.sleep(0.5)
    
    # ========================================================================
    # PROCESAMIENTO DE SEÑALES
    # ========================================================================
    
    async def _process_normal_signal(self, message_id: str, message_data: Dict):
        """Procesa una señal normal del stream."""
        try:
            signal_data = json.loads(message_data.get("data", "{}"))
            
            if "timestamp" in signal_data and isinstance(signal_data["timestamp"], str):
                signal_data["timestamp"] = datetime.fromisoformat(
                    signal_data["timestamp"].replace('Z', '+00:00')
                )
            
            signal = Signal(**signal_data)
            
            # 1. Persistir señal
            signal_id = await self._persist_signal(signal)
            
            # 2. Obtener reglas y evaluar
            reglas = await self._get_rules(signal.vehicle_id)
            await self._evaluate_complex_rules(signal, signal_id, reglas)
            
            # 3. ACK
            await self.redis.xack(REDIS_STREAM_NAME, "ccs_workers", message_id)
            
            # 4. Actualizar métricas
            self.metrics["signals_processed"] += 1
            
        except Exception as e:
            logger.error(f"❌ Error procesando señal normal {message_id}: {e}")
    
    async def _process_emergency_signal(self, message_id: str, message_data: Dict):
        """Procesa una señal de emergencia."""
        try:
            signal_data = json.loads(message_data.get("data", "{}"))
            
            if "timestamp" in signal_data and isinstance(signal_data["timestamp"], str):
                signal_data["timestamp"] = datetime.fromisoformat(
                    signal_data["timestamp"].replace('Z', '+00:00')
                )
            
            signal = Signal(**signal_data)
            
            # EMERGENCIA: Procesar inmediatamente
            start_time = datetime.utcnow()
            
            # 1. Persistir señal (más rápido, sin validaciones complejas)
            signal_id = await self._persist_emergency_signal(signal)
            
            # 2. Obtener solo reglas de emergencia
            reglas = await self._get_emergency_rules(signal.vehicle_id)
            
            # 3. Evaluar reglas (solo PANIC_BUTTON)
            await self._evaluate_emergency_rules(signal, signal_id, reglas)
            
            # 4. ACK inmediato
            await self.redis.xack(EMERGENCY_STREAM_NAME, "ccs_emergency_workers", message_id)
            
            # 5. Actualizar métricas
            self.metrics["emergencies_processed"] += 1
            self.metrics["last_emergency_time"] = datetime.utcnow()
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"🚨 Emergencia procesada en {processing_time:.3f}s - Vehículo: {signal.vehicle_id}")
            
            if processing_time > 2.0:
                logger.error(f"❌ ALERTA: Emergencia tardó {processing_time:.3f}s (>2s límite)")
            
        except Exception as e:
            logger.error(f"❌ CRÍTICO: Error procesando emergencia {message_id}: {e}")
    
    # ========================================================================
    # REGLAS COMPLEJAS
    # ========================================================================
    
    async def _evaluate_complex_rules(self, signal: Signal, signal_id: int, reglas: List[Dict]):
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
                if signal.vehicle_id in self.geofence_cache:
                    geofences = self.geofence_cache[signal.vehicle_id]
                    if await self._check_geofence_violation(signal, geofences, regla["comparison_value"]):
                        violation = True
                        mensaje = f"Salida de zona: {regla['comparison_value']}"
            
            # SCHEDULE (Horario no permitido)
            elif rule_type == RuleType.SCHEDULE:
                if signal.vehicle_id in self.schedule_cache:
                    schedule = self.schedule_cache[signal.vehicle_id]
                    if await self._check_schedule_violation(signal, schedule):
                        violation = True
                        mensaje = f"Movimiento en horario no permitido: {schedule.get('start_time')}-{schedule.get('end_time')}"
            
            # UNPLANNED STOP (Detención no planeada)
            elif rule_type == RuleType.UNPLANNED_STOP:
                if await self._check_unplanned_stop(signal):
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
                await self._send_notification(signal.vehicle_id, mensaje, regla["action_type"])
        
        # BULK INSERT ALERTAS
        if alerts_to_insert:
            try:
                async with self.pool.acquire() as conn:
                    await conn.executemany("""
                        INSERT INTO alerts (vehicle_id, rule_id, signal_id, message, action_taken, timestamp)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, alerts_to_insert)
                    self.metrics["alerts_generated"] += len(alerts_to_insert)
            except Exception as e:
                logger.error(f"❌ Error insertando alertas: {e}")
    
    async def _evaluate_emergency_rules(self, signal: Signal, signal_id: int, reglas: List[Dict]):
        """Evalúa solo reglas de emergencia (más rápido)."""
        for regla in reglas:
            if regla["rule_type"] == RuleType.PANIC_BUTTON and signal.panic_button:
                mensaje = "🚨 EMERGENCIA: Botón de pánico activado"
                logger.critical(mensaje)
                
                try:
                    async with self.pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO alerts (vehicle_id, rule_id, signal_id, message, action_taken, timestamp)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """, signal.vehicle_id, regla["id"], signal_id, mensaje, regla["action_type"], datetime.utcnow())
                        
                        self.metrics["alerts_generated"] += 1
                        
                    # Notificación inmediata
                    await self._send_emergency_notification(signal.vehicle_id, mensaje)
                    
                except Exception as e:
                    logger.error(f"❌ Error en emergencia: {e}")
    
    # ========================================================================
    # UTILIDADES DE REGLAS COMPLEJAS
    # ========================================================================
    
    async def _check_geofence_violation(self, signal: Signal, geofences: List, zone_name: str) -> bool:
        """Verifica si el vehículo salió de una geocerca."""
        try:
            for geofence in geofences:
                if geofence.get('name') == zone_name and geofence.get('is_allowed', True):
                    center = geofence.get('center', {})
                    radius_km = geofence.get('radius_km', 0)
                    
                    # Calcular distancia al centro
                    distance = self._calculate_distance(
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
    
    async def _check_schedule_violation(self, signal: Signal, schedule: Dict) -> bool:
        """Verifica si el vehículo se mueve fuera del horario permitido."""
        try:
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
    
    async def _check_unplanned_stop(self, signal: Signal) -> bool:
        """Detecta detenciones no planeadas."""
        try:
            # Obtener últimas señales del vehículo
            async with self.pool.acquire() as conn:
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
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
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
    
    # ========================================================================
    # MÉTODOS DE PERSISTENCIA Y CACHE
    # ========================================================================
    
    async def _persist_signal(self, signal: Signal) -> int:
        """Guarda señal en PostgreSQL."""
        metadata = {
            **signal.metadata,
            "panic_button": signal.panic_button,
            "temperature": signal.temperature,
            "vehicle_type": signal.vehicle_type.value if signal.vehicle_type else None,
            "processed_at": datetime.utcnow().isoformat(),
            "api_instance": self.api_instance_id
        }
        
        async with self.pool.acquire() as conn:
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
    
    async def _persist_emergency_signal(self, signal: Signal) -> int:
        """Guarda señal de emergencia (más rápido, menos validaciones)."""
        async with self.pool.acquire() as conn:
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
    
    async def _get_rules(self, vehicle_id: str) -> List[Dict]:
        """Obtiene todas las reglas activas para un vehículo."""
        cache_key = f"rules:{vehicle_id}"
        
        if self.redis_enabled:
            try:
                cached = await asyncio.wait_for(self.redis.get(cache_key), timeout=0.5)
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
            async with self.pool.acquire() as conn:
                rows = await asyncio.wait_for(conn.fetch(query, vehicle_id), timeout=1.0)
        except asyncio.TimeoutError:
            return []
        except Exception as e:
            logger.error(f"❌ Error obteniendo reglas: {e}")
            return []
        
        reglas = [dict(fila) for fila in rows]

        if reglas and self.redis_enabled:
            try:
                await asyncio.wait_for(
                    self.redis.setex(cache_key, 300, json.dumps(reglas, default=str)),
                    timeout=0.3
                )
            except:
                pass
        
        return reglas
    
    async def _get_emergency_rules(self, vehicle_id: str) -> List[Dict]:
        """Obtiene solo reglas de emergencia (PANIC_BUTTON)."""
        cache_key = f"emergency_rules:{vehicle_id}"
        
        if self.redis_enabled:
            try:
                cached = await asyncio.wait_for(self.redis.get(cache_key), timeout=0.1)
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
            async with self.pool.acquire() as conn:
                rows = await asyncio.wait_for(conn.fetch(query, vehicle_id), timeout=0.5)
        except asyncio.TimeoutError:
            return []
        
        reglas = [dict(fila) for fila in rows]

        if reglas and self.redis_enabled:
            try:
                await asyncio.wait_for(
                    self.redis.setex(cache_key, 600, json.dumps(reglas, default=str)),
                    timeout=0.1
                )
            except:
                pass
        
        return reglas
    
    # ========================================================================
    # NOTIFICACIONES
    # ========================================================================
    
    async def _send_notification(self, vehicle_id: str, mensaje: str, accion: str):
        """Envía notificación al propietario."""
        try:
            async with self.pool.acquire() as conn:
                # Obtener propietario
                owner = await conn.fetchrow("""
                    SELECT o.id, o.full_name, o.email, o.phone
                    FROM owners o
                    JOIN vehicles v ON v.owner_id = o.id
                    WHERE v.id = $1
                """, vehicle_id)
                
                if owner:
                    # Determinar canal según acción
                    if accion in [ActionType.NOTIFY_POLICE, ActionType.CALL_EMERGENCY]:
                        channel = "emergency_services"
                        logger.critical(f"🚨 CONTACTANDO AUTORIDADES: {mensaje}")
                    elif accion == ActionType.NOTIFY_OWNER:
                        channel = "owner_sms"
                        logger.info(f"📱 SMS a {owner['phone']}: {mensaje}")
                    elif accion == ActionType.SMS_OWNER:
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
    
    async def _send_emergency_notification(self, vehicle_id: str, mensaje: str):
        """Envía notificación de emergencia (más rápido)."""
        try:
            async with self.pool.acquire() as conn:
                owner = await conn.fetchrow("""
                    SELECT o.phone FROM owners o
                    JOIN vehicles v ON v.owner_id = o.id
                    WHERE v.id = $1
                """, vehicle_id)
                
                if owner:
                    logger.critical(f"🚨 EMERGENCIA - Contactando a {owner['phone']}: {mensaje}")
                    
                    # Aquí se integraría con servicio real de SMS/llamada
                    # Por ahora solo log
                    
        except Exception as e:
            logger.error(f"❌ Error en notificación de emergencia: {e}")

state = GlobalState()

# ============================================================================
# LIFESPAN MANAGER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager para FastAPI.
    
    Inicializa el estado global al inicio y lo limpia al final.
    """
    logger.info("🔄 Iniciando lifespan manager...")
    await state.initialize()
    yield
    logger.info("🔄 Finalizando lifespan manager...")
    await state.shutdown()

# ============================================================================
# FASTAPI APP CON DOCUMENTACIÓN MEJORADA
# ============================================================================

app = FastAPI(
    title="CCS Central API - Sistema de Monitoreo Vehicular",
    version="4.0",
    description="""
    ## 📡 API Central de CCS (Compañía Colombiana de Seguimiento)
    
    Sistema de monitoreo en tiempo real para vehículos de carga, transporte público y particulares.
    
    ### 🎯 Características principales:
    - Procesamiento de 500+ señales por segundo
    - Respuesta a emergencias en menos de 2 segundos
    - Reglas complejas: Geocercas, Horarios, Temperatura, Detenciones
    - Notificaciones multi-canal (SMS, Email, Autoridades)
    - Escalabilidad horizontal
    
    ### 📊 Estadísticas actuales:
    - 1,500 camiones
    - 5,000 vehículos
    - 3,000 motocicletas
    - Crecimiento anual del 20%
    
    ### 🔧 Stack tecnológico:
    - FastAPI (Python 3.9+)
    - PostgreSQL con particionamiento temporal
    - Redis para streams y cache
    - Docker para contenerización
    """,
    contact={
        "name": "Equipo CCS",
        "email": "soporte@ccs.com.co",
        "url": "https://api.ccs.com.co/docs"
    },
    license_info={
        "name": "CCS Internal API License",
        "url": "https://ccs.com.co/license"
    },
    openapi_tags=[
        {
            "name": "signals",
            "description": "Endpoints para recepción y procesamiento de señales"
        },
        {
            "name": "rules",
            "description": "Gestión de reglas de negocio y configuración"
        },
        {
            "name": "monitoring",
            "description": "Monitoreo del sistema y métricas"
        },
        {
            "name": "geofences",
            "description": "Gestión de geocercas y zonas"
        },
        {
            "name": "schedules",
            "description": "Gestión de horarios y tiempos permitidos"
        }
    ],
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# ============================================================================
# ENDPOINTS PRINCIPALES
# ============================================================================

@app.post(
    "/signal",
    response_model=SignalResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["signals"],
    summary="Procesar señal de vehículo",
    description="""
    Recibe y procesa una señal de telemetría de un vehículo.
    
    ### Flujo de procesamiento:
    1. Validación de datos de entrada
    2. Determinación de prioridad (normal/emergencia)
    3. Publicación en stream correspondiente
    4. Respuesta inmediata al cliente
    5. Procesamiento asíncrono por workers
    
    ### Prioridades:
    - **Normal**: Señales regulares de telemetría
    - **Emergency**: Botón de pánico activado (procesado en <2s)
    
    ### Ejemplos de uso:
    - Camión refrigerado reportando temperatura
    - Taxi activando botón de pánico
    - Motocicleta reportando posición y velocidad
    """,
    responses={
        202: {
            "description": "Señal aceptada para procesamiento",
            "content": {
                "application/json": {
                    "example": {
                        "status": "accepted",
                        "vehicle_id": "TRUCK-001",
                        "message_id": "1705311000000-0",
                        "processing_time_ms": 12.5,
                        "timestamp": "2024-01-15T10:30:00Z",
                        "priority": "normal"
                    }
                }
            }
        },
        503: {
            "description": "Servicio temporalmente no disponible",
            "content": {
                "application/json": {
                    "example": {"detail": "Redis deshabilitado temporalmente"}
                }
            }
        }
    }
)
async def process_signal(signal: Signal = Body(..., example={
    "vehicle_id": "TRUCK-011",
    "speed": 65.5,
    "latitude": 4.60971,
    "longitude": -74.08175,
    "timestamp": "2024-01-15T10:30:00Z",
    "panic_button": False,
    "temperature": -15.0,
    "vehicle_type": "TRUCK",
    "metadata": {
        "cargo_type": "pharmaceuticals",
        "door_status": "closed"
    }
})):
    """
    Endpoint principal para recibir señales de vehículos.
    """
    if not state.redis_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis deshabilitado temporalmente"
        )
    
    start_time = datetime.utcnow()
    
    try:
        # Determinar prioridad
        is_emergency = signal.panic_button
        
        if is_emergency:
            # Stream de emergencia (alta prioridad)
            stream_name = EMERGENCY_STREAM_NAME
            priority = "emergency"
        else:
            # Stream normal
            stream_name = REDIS_STREAM_NAME
            priority = "normal"
        
        # Publicar en stream
        message_id = await state.redis.xadd(
            stream_name,
            {"data": json.dumps(signal.to_json_serializable_dict())},
            maxlen=10000
        )
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return SignalResponse(
            status="accepted",
            vehicle_id=signal.vehicle_id,
            message_id=message_id,
            processing_time_ms=round(processing_time, 2),
            timestamp=datetime.utcnow(),
            priority=priority
        )
        
    except Exception as e:
        logger.error(f"❌ Error procesando señal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.post(
    "/geofence",
    status_code=status.HTTP_201_CREATED,
    tags=["geofences"],
    summary="Definir geocerca para vehículo",
    description="""
    Define una geocerca (zona geográfica) para un vehículo.
    
    Una geocerca puede ser:
    - **Permitida**: Vehículo debe permanecer dentro
    - **Prohibida**: Vehículo no debe entrar
    
    ### Ejemplos de uso:
    - Camión de obra debe permanecer en zona de construcción
    - Taxi no puede salir del área metropolitana
    - Motocicleta de domicilios restringida a zona norte
    """,
    responses={
        201: {
            "description": "Geocerca creada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "created",
                        "geofence_id": "zone_norte_001",
                        "vehicle_id": "TRUCK-001",
                        "message": "Geocerca 'Zona_Norte' definida exitosamente"
                    }
                }
            }
        }
    }
)
async def define_geofence(geofence_def: GeofenceDefinition):
    """
    Define una nueva geocerca para un vehículo.
    """
    try:
        # Actualizar cache en memoria
        if geofence_def.vehicle_id not in state.geofence_cache:
            state.geofence_cache[geofence_def.vehicle_id] = []
        
        state.geofence_cache[geofence_def.vehicle_id].append(
            geofence_def.geofence.dict()
        )
        
        # Persistir en base de datos (simulado)
        async with state.pool.acquire() as conn:
            # Actualizar metadata del vehículo
            await conn.execute("""
                UPDATE vehicles 
                SET details = jsonb_set(
                    COALESCE(details, '{}'::jsonb),
                    '{geofences}',
                    $1::jsonb
                )
                WHERE id = $2
            """, json.dumps(state.geofence_cache[geofence_def.vehicle_id]), geofence_def.vehicle_id)
        
        return {
            "status": "created",
            "geofence_id": f"{geofence_def.geofence.name}_{geofence_def.vehicle_id}",
            "vehicle_id": geofence_def.vehicle_id,
            "message": f"Geocerca '{geofence_def.geofence.name}' definida exitosamente"
        }
        
    except Exception as e:
        logger.error(f"❌ Error definiendo geocerca: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error definiendo geocerca: {str(e)}"
        )

@app.post(
    "/schedule",
    status_code=status.HTTP_201_CREATED,
    tags=["schedules"],
    summary="Definir horario permitido para vehículo",
    description="""
    Define el horario permitido de operación para un vehículo.
    
    ### Parámetros:
    - **start_time**: Hora de inicio (HH:MM)
    - **end_time**: Hora de fin (HH:MM)
    - **days_of_week**: Días permitidos (1=Lunes, 7=Domingo)
    
    ### Ejemplos de uso:
    - Motocicletas de domicilios solo de 6:00 a 22:00
    - Camiones de basura solo de lunes a viernes
    - Vehículos de empresa con horario comercial
    """,
    responses={
        201: {
            "description": "Horario definido exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "created",
                        "schedule_id": "schedule_moto_001",
                        "vehicle_id": "MOTO-301",
                        "message": "Horario 06:00-22:00 definido para Lunes-Viernes"
                    }
                }
            }
        }
    }
)
async def define_schedule(schedule_def: ScheduleDefinition):
    """
    Define un horario permitido para un vehículo.
    """
    try:
        # Actualizar cache en memoria
        state.schedule_cache[schedule_def.vehicle_id] = schedule_def.schedule.dict()
        
        # Persistir en base de datos (simulado)
        async with state.pool.acquire() as conn:
            await conn.execute("""
                UPDATE vehicles 
                SET details = jsonb_set(
                    COALESCE(details, '{}'::jsonb),
                    '{schedule}',
                    $1::jsonb
                )
                WHERE id = $2
            """, json.dumps(schedule_def.schedule.dict()), schedule_def.vehicle_id)
        
        days_str = {
            1: "Lunes", 2: "Martes", 3: "Miércoles", 
            4: "Jueves", 5: "Viernes", 6: "Sábado", 7: "Domingo"
        }
        allowed_days = [days_str[d] for d in schedule_def.schedule.days_of_week]
        
        return {
            "status": "created",
            "schedule_id": f"schedule_{schedule_def.vehicle_id}",
            "vehicle_id": schedule_def.vehicle_id,
            "message": f"Horario {schedule_def.schedule.start_time}-{schedule_def.schedule.end_time} definido para {', '.join(allowed_days)}"
        }
        
    except Exception as e:
        logger.error(f"❌ Error definiendo horario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error definiendo horario: {str(e)}"
        )

@app.post(
    "/update-rule",
    tags=["rules"],
    summary="Actualizar regla existente",
    description="""
    Actualiza los parámetros de una regla existente.
    
    ### Campos actualizables:
    - **comparison_value**: Nuevo valor de comparación
    - **action_type**: Nueva acción a tomar
    - **is_active**: Activar/desactivar regla
    """,
    responses={
        200: {
            "description": "Regla actualizada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Regla MAX_SPEED actualizada a 90.0 km/h",
                        "rows_updated": "1"
                    }
                }
            }
        }
    }
)
async def update_rule(update: RuleUpdate):
    """
    Actualiza una regla existente.
    """
    try:
        async with state.pool.acquire() as conn:
            rows_updated = await conn.execute("""
                UPDATE rules 
                SET comparison_value = $1, 
                    action_type = $2,
                    is_active = $3
                WHERE vehicle_id = $4 AND rule_type = $5
            """, 
                update.comparison_value,
                update.action_type.value,
                update.is_active,
                update.vehicle_id,
                update.rule_type.value
            )
        
        # Invalidar cache
        if state.redis_enabled:
            try:
                await state.redis.delete(f"rules:{update.vehicle_id}")
                await state.redis.delete(f"emergency_rules:{update.vehicle_id}")
            except:
                pass
        
        return {
            "status": "success",
            "message": f"Regla {update.rule_type.value} actualizada a {update.comparison_value}",
            "rows_updated": rows_updated.split()[1] if ' ' in rows_updated else rows_updated,
        }
        
    except Exception as e:
        logger.error(f"❌ Error actualizando regla: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando regla: {str(e)}"
        )

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["monitoring"],
    summary="Verificar estado del sistema",
    description="""
    Verifica el estado de salud de todos los componentes del sistema.
    
    ### Componentes monitoreados:
    - **PostgreSQL**: Base de datos principal
    - **Redis**: Cache y streams
    - **Streams**: Estado de los streams de procesamiento
    
    ### Métricas incluidas:
    - Señales procesadas
    - Alertas generadas
    - Emergencias atendidas
    - Tiempo de actividad
    """,
    responses={
        200: {
            "description": "Estado del sistema",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "services": {
                            "postgresql": "healthy",
                            "redis": "healthy",
                            "stream_normal": "healthy",
                            "stream_emergency": "healthy"
                        },
                        "uptime_seconds": 86400.5,
                        "timestamp": "2024-01-15T10:30:00Z",
                        "metrics": {
                            "signals_processed": 15000,
                            "alerts_generated": 450,
                            "emergencies_processed": 12,
                            "last_emergency_time": "2024-01-15T10:25:30Z"
                        }
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Health check completo del sistema.
    """
    try:
        # Verificar PostgreSQL
        async with state.pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
            pg_status = "healthy"
    except:
        pg_status = "unhealthy"
    
    try:
        if state.redis_enabled:
            await state.redis.ping()
            redis_status = "healthy"
        else:
            redis_status = "circuit_open"
    except:
        redis_status = "unhealthy"
    
    # Verificar streams
    try:
        stream_info = await state.redis.xinfo_stream(REDIS_STREAM_NAME)
        stream_normal_status = "healthy"
    except:
        stream_normal_status = "unhealthy"
    
    try:
        stream_info = await state.redis.xinfo_stream(EMERGENCY_STREAM_NAME)
        stream_emergency_status = "healthy"
    except:
        stream_emergency_status = "unhealthy"
    
    # Determinar estado general
    services_status = {
        "postgresql": pg_status,
        "redis": redis_status,
        "stream_normal": stream_normal_status,
        "stream_emergency": stream_emergency_status
    }
    
    if all(status == "healthy" for service, status in services_status.items() 
           if service != "redis" or redis_status in ["healthy", "circuit_open"]):
        overall_status = "healthy"
    elif any(status == "unhealthy" for status in services_status.values()):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    uptime = (datetime.utcnow() - state.start_time).total_seconds()
    
    return HealthResponse(
        status=overall_status,
        services=services_status,
        uptime_seconds=round(uptime, 2),
        timestamp=datetime.utcnow(),
        metrics=state.metrics
    )

@app.get(
    "/metrics",
    tags=["monitoring"],
    summary="Obtener métricas detalladas del sistema",
    description="""
    Obtiene métricas detalladas de rendimiento y uso del sistema.
    
    ### Métricas incluidas:
    - Procesamiento de señales
    - Generación de alertas
    - Tiempos de respuesta
    - Uso de recursos
    - Estados de colas
    """
)
async def get_metrics():
    """
    Obtiene métricas detalladas del sistema.
    """
    try:
        # Obtener métricas de Redis
        redis_info = {}
        if state.redis_enabled:
            try:
                redis_info = await state.redis.info()
            except:
                redis_info = {"error": "No disponible"}
        
        # Obtener métricas de PostgreSQL
        db_metrics = {}
        try:
            async with state.pool.acquire() as conn:
                # Señales por hora
                signals_per_hour = await conn.fetchval("""
                    SELECT COUNT(*) / 24.0 
                    FROM signals 
                    WHERE timestamp > NOW() - INTERVAL '24 hours'
                """) or 0
                
                # Alertas recientes
                recent_alerts = await conn.fetchval("""
                    SELECT COUNT(*) 
                    FROM alerts 
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                """) or 0
                
                db_metrics = {
                    "signals_per_hour": round(float(signals_per_hour), 2),
                    "recent_alerts": recent_alerts,
                    "total_vehicles": await conn.fetchval("SELECT COUNT(*) FROM vehicles"),
                    "active_rules": await conn.fetchval("SELECT COUNT(*) FROM rules WHERE is_active = TRUE")
                }
        except:
            db_metrics = {"error": "No disponible"}
        
        return {
            "system": {
                "uptime_seconds": round((datetime.utcnow() - state.start_time).total_seconds(), 2),
                "api_instance": state.api_instance_id,
                "timestamp": datetime.utcnow().isoformat()
            },
            "processing": state.metrics,
            "database": db_metrics,
            "redis": {
                "enabled": state.redis_enabled,
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_mb": round(redis_info.get("used_memory", 0) / (1024*1024), 2) if redis_info.get("used_memory") else 0
            },
            "queues": {
                "normal_pending": await state.redis.xpending(REDIS_STREAM_NAME, "ccs_workers") if state.redis_enabled else 0,
                "emergency_pending": await state.redis.xpending(EMERGENCY_STREAM_NAME, "ccs_emergency_workers") if state.redis_enabled else 0
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo métricas: {str(e)}"
        )

# ============================================================================
# EJECUCIÓN PRINCIPAL
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        limit_concurrency=1000,
        timeout_keep_alive=30,
        access_log=True
    )