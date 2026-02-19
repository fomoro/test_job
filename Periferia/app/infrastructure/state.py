"""
infrastructure/state.py - Estado global y conexiones a servicios externos
"""

import os
import json
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List

import asyncpg
from redis.asyncio import Redis
from dotenv import load_dotenv

from application.services import (
    RuleService, NotificationService, DataService
)
from domain.models import Signal

load_dotenv('.env')

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
REDIS_STREAM_NAME = os.getenv('REDIS_STREAM_NAME', 'ccs_signals_stream')
EMERGENCY_STREAM_NAME = os.getenv('EMERGENCY_STREAM_NAME', 'ccs_emergency_stream')
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/ccs_local')

logger = logging.getLogger(__name__)


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
            signal_id = await DataService.persist_signal(signal, self.pool, self.api_instance_id)
            
            # 2. Obtener reglas y evaluar
            reglas = await DataService.get_rules(signal.vehicle_id, self.pool, self.redis, self.redis_enabled)
            
            # 3. Evaluar reglas complejas
            alerts_to_insert = await RuleService.evaluate_complex_rules(
                signal, signal_id, reglas,
                self.geofence_cache, self.schedule_cache,
                self.pool, self.redis_enabled, self.metrics
            )
            
            # 4. Insertar alertas
            if alerts_to_insert:
                await DataService.bulk_insert_alerts(alerts_to_insert, self.pool)
            
            # 5. ACK
            await self.redis.xack(REDIS_STREAM_NAME, "ccs_workers", message_id)
            
            # 6. Actualizar métricas
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
            
            # 1. Persistir señal (más rápido)
            signal_id = await DataService.persist_emergency_signal(signal, self.pool)
            
            # 2. Obtener solo reglas de emergencia
            reglas = await DataService.get_emergency_rules(
                signal.vehicle_id, self.pool, self.redis, self.redis_enabled
            )
            
            # 3. Evaluar reglas de emergencia
            await RuleService.evaluate_emergency_rules(
                signal, signal_id, reglas, self.pool, self.metrics
            )
            
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


# Instancia global del estado
state = GlobalState()