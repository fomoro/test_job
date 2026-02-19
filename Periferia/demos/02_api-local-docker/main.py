import os
import json
import logging
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import asyncpg
from redis.asyncio import Redis
from dotenv import load_dotenv

# Configuración de Logs optimizada para producción
logging.basicConfig(
    level=logging.WARNING,  # Reducido de INFO a WARNING para menos ruido
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class GlobalState:
    pool: asyncpg.Pool = None
    redis: Redis = None
    redis_enabled: bool = True  # Circuit breaker flag

state = GlobalState()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🔌 Conectando a NeonDB y Upstash...")
    try:
        # ✅ POOL AUMENTADO: 100 conexiones máximas para 500 RPS
        state.pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL"), 
            min_size=10, 
            max_size=100,  # 🔥 10x más que antes
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=60  # Timeout por comando
        )
        
        # ✅ REDIS con configuración optimizada
        state.redis = Redis.from_url(
            os.getenv("REDIS_URL"), 
            decode_responses=True,
            socket_timeout=2,      # 2 segundos máximo por operación
            socket_connect_timeout=2,
            retry_on_timeout=True,
            max_connections=50     # Más conexiones para Redis también
        )
        
        # Test rápido de conexiones
        await state.redis.ping()
        logger.info("✅ Conexiones establecidas (PostgreSQL: 100, Redis: 50)")
        
        yield
    except Exception as e:
        logger.error(f"❌ Error crítico al iniciar: {e}")
        raise e
    finally:
        logger.info("🔒 Cerrando conexiones...")
        if state.pool: 
            await state.pool.close()
        if state.redis: 
            await state.redis.close()

app = FastAPI(lifespan=lifespan, title="CCS Central Optimizada", version="2.0")

# --- MODELOS (sin cambios) ---
class Signal(BaseModel):
    vehicle_id: str
    speed: float
    latitude: float
    longitude: float
    timestamp: datetime = Field(default_factory=datetime.now)
    panic_button: bool = False
    metadata: Dict[str, Any] = {}

class RuleUpdate(BaseModel):
    vehicle_id: str
    new_limit: float

# --- HEALTH CHECK MEJORADO ---
@app.get("/health")
async def health_check():
    metrics = {}
    
    try:
        async with state.pool.acquire() as conn:
            # Verificar estadísticas del pool
            pool_stats = await conn.fetchval("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
            metrics["pg_active_connections"] = pool_stats
            pg_status = "healthy"
    except Exception as e:
        pg_status = "unhealthy"
        metrics["pg_error"] = str(e)
    
    try:
        if state.redis_enabled:
            redis_info = await state.redis.info('memory')
            metrics["redis_memory"] = redis_info.get('used_memory_human', 'N/A')
            redis_status = "healthy"
        else:
            redis_status = "circuit_open"
            metrics["redis_status"] = "circuit_breaker_active"
    except:
        redis_status = "unhealthy"
    
    overall = "healthy" if pg_status == "healthy" and redis_status in ["healthy", "circuit_open"] else "degraded"
    
    return {
        "status": overall,
        "services": {"postgresql": pg_status, "redis": redis_status},
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }

# --- LÓGICA DE NEGOCIO OPTIMIZADA ---
async def obtener_reglas(vehicle_id: str) -> List[Dict]:
    """Obtiene reglas con timeout agresivo y circuit breaker."""
    clave_redis = f"rules:{vehicle_id}"
    
    # ✅ INTENTAR REDIS PRIMERO (con timeout de 500ms)
    if state.redis_enabled:
        try:
            datos_cache = await asyncio.wait_for(
                state.redis.get(clave_redis),
                timeout=0.5  # 🔥 500ms máximo para Redis
            )
            if datos_cache:
                logger.debug(f"✅ CACHE HIT: {vehicle_id}")
                return json.loads(datos_cache)
        except asyncio.TimeoutError:
            logger.warning(f"⚠️ Redis timeout para {vehicle_id}, deshabilitando temporalmente")
            state.redis_enabled = False
        except Exception as e:
            logger.debug(f"Redis falló: {e}")
    
    # ✅ CACHE MISS: Ir a PostgreSQL
    logger.info(f"💨 CACHE MISS: {vehicle_id} -> DB")
    
    query = """
        SELECT id, rule_type, comparison_value, action_type 
        FROM rules 
        WHERE vehicle_id = $1 AND is_active = TRUE
    """
    
    try:
        async with state.pool.acquire() as conn:
            # Timeout de 1 segundo para consulta
            filas = await asyncio.wait_for(
                conn.fetch(query, vehicle_id),
                timeout=1.0
            )
    except asyncio.TimeoutError:
        logger.error(f"❌ Timeout consultando reglas para {vehicle_id}")
        return []  # Mejor devolver vacío que bloquear
    except Exception as e:
        logger.error(f"❌ Error BD reglas: {e}")
        return []
    
    reglas = [dict(fila) for fila in filas]

    # ✅ REINTENTAR GUARDAR EN REDIS (si está habilitado)
    if reglas and state.redis_enabled:
        try:
            await asyncio.wait_for(
                state.redis.setex(clave_redis, 300, json.dumps(reglas, default=str)),
                timeout=0.3  # 300ms máximo para guardar
            )
        except:
            pass  # Silenciosamente fallar, no es crítico
    
    return reglas

# --- ENDPOINT PRINCIPAL SUPER OPTIMIZADO ---
@app.post("/signal")
async def procesar_señal(senal: Signal):
    start_time = datetime.now()
    
    try:
        # ✅ EJECUCIÓN PARALELA: Insertar señal Y obtener reglas al mismo tiempo
        async with state.pool.acquire() as conn:
            # Crear tareas paralelas
            insert_task = asyncio.wait_for(
                conn.fetchval("""
                    INSERT INTO signals (vehicle_id, timestamp, latitude, longitude, speed, heading, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, 
                senal.vehicle_id,
                senal.timestamp,
                senal.latitude,
                senal.longitude,
                senal.speed,
                0.0,  # heading por defecto
                json.dumps(senal.metadata)
                ),
                timeout=1.5  # 🔥 Timeout agresivo
            )
            
            rules_task = obtener_reglas(senal.vehicle_id)
            
            # Ejecutar ambas en paralelo
            try:
                signal_id, reglas = await asyncio.gather(insert_task, rules_task)
                logger.debug(f"📡 Señal insertada ID: {signal_id}")
            except asyncio.TimeoutError as e:
                # Si el INSERT timeout, continuar sin signal_id
                logger.warning(f"⚠️ Timeout insertando señal: {e}")
                signal_id = None
                reglas = await rules_task  # Aún obtener reglas
            except Exception as e:
                logger.error(f"❌ Error paralelo: {e}")
                signal_id = None
                reglas = []
        
        alertas_generadas = []
        alertas_a_insertar = []  # Para bulk insert
        
        # ✅ EVALUAR REGLAS RÁPIDAMENTE
        for regla in reglas:
            violation = False
            mensaje = ""
            
            if regla["rule_type"] == "MAX_SPEED":
                limite = float(regla["comparison_value"])
                if senal.speed > limite:
                    violation = True
                    mensaje = f"Exceso velocidad: {senal.speed} > {limite}"

            elif regla["rule_type"] == "PANIC_BUTTON" and senal.panic_button:
                violation = True
                mensaje = "🚨 BOTÓN DE PÁNICO ACTIVADO"

            # ✅ PREPARAR PARA BULK INSERT
            if violation:
                logger.warning(f"🛑 ALERTA: {mensaje}")
                alertas_a_insertar.append((
                    senal.vehicle_id, 
                    regla["id"],
                    signal_id,
                    mensaje, 
                    regla["action_type"],
                    senal.timestamp
                ))
                
                alertas_generadas.append({
                    "rule": regla["rule_type"],
                    "action": regla["action_type"],
                    "message": mensaje,
                    "signal_id": signal_id
                })
        
        # ✅ BULK INSERT DE ALERTAS (si hay)
        if alertas_a_insertar:
            try:
                async with state.pool.acquire() as conn:
                    await conn.executemany("""
                        INSERT INTO alerts (vehicle_id, rule_id, signal_id, message, action_taken, timestamp)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, alertas_a_insertar)
                    logger.debug(f"📊 Bulk insert: {len(alertas_a_insertar)} alertas")
            except asyncio.TimeoutError:
                logger.error("❌ Timeout insertando alertas")
            except Exception as e:
                logger.error(f"❌ Error bulk insert: {e}")
        
        # ✅ CALCULAR MÉTRICAS
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Verificar cache status rápidamente
        cache_status = "error"
        if state.redis_enabled:
            try:
                exists = await asyncio.wait_for(
                    state.redis.exists(f"rules:{senal.vehicle_id}"),
                    timeout=0.1
                )
                cache_status = "hit" if exists else "miss"
            except:
                cache_status = "timeout"
        
        # ✅ VALIDAR SLA INTERNO
        sla_status = "ok" if processing_time < 2000 else "violated"
        
        return {
            "status": "processed",
            "sla": sla_status,
            "vehicle_id": senal.vehicle_id,
            "signal_id": signal_id,
            "alerts_generated": len(alertas_generadas),
            "alerts": alertas_generadas,
            "processing_time_ms": round(processing_time, 2),
            "cache_status": cache_status,
            "timestamp": datetime.now().isoformat()
        }

    except asyncpg.PostgresError as e:
        logger.error(f"❌ Error PostgreSQL: {e}")
        # Respuesta rápida incluso en error
        return {
            "status": "error",
            "message": "Error de base de datos",
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
        }
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}")
        return {
            "status": "error",
            "message": str(e),
            "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
        }

# --- ACTUALIZAR REGLA OPTIMIZADA ---
@app.post("/update-rule")
async def actualizar_regla(update: RuleUpdate):
    logger.info(f"📝 Actualizando regla para {update.vehicle_id}...")
    start_time = datetime.now()

    try:
        async with state.pool.acquire() as conn:
            rows_updated = await conn.execute("""
                UPDATE rules 
                SET comparison_value = $1 
                WHERE vehicle_id = $2 AND rule_type = 'MAX_SPEED'
            """, str(update.new_limit), update.vehicle_id)
        
        # ✅ INVALIDACIÓN DE CACHE CON TIMEOUT
        clave_redis = f"rules:{update.vehicle_id}"
        deleted = 0
        if state.redis_enabled:
            try:
                deleted = await asyncio.wait_for(
                    state.redis.delete(clave_redis),
                    timeout=0.3
                )
            except:
                pass  # No crítico si falla
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "status": "success",
            "message": f"Regla actualizada a {update.new_limit} km/h",
            "cache_invalidated": deleted > 0,
            "rows_updated": rows_updated.split()[1] if ' ' in rows_updated else rows_updated,
            "processing_time_ms": round(processing_time, 2)
        }

    except Exception as e:
        logger.error(f"❌ Error actualizando regla: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ESTADÍSTICAS OPTIMIZADAS ---
@app.get("/stats")
async def get_stats():
    try:
        start_time = datetime.now()
        
        # ✅ CONSULTAS PARALELAS
        async with state.pool.acquire() as conn:
            # Ejecutar múltiples consultas en paralelo
            total_vehicles_task = conn.fetchval("SELECT COUNT(*) FROM vehicles WHERE active = TRUE")
            total_rules_task = conn.fetchval("SELECT COUNT(*) FROM rules WHERE is_active = TRUE")
            total_alerts_task = conn.fetchval("SELECT COUNT(*) FROM alerts")
            alerts_with_signal_task = conn.fetchval("SELECT COUNT(*) FROM alerts WHERE signal_id IS NOT NULL")
            top_offenders_task = conn.fetch("""
                SELECT vehicle_id, COUNT(*) as alert_count 
                FROM alerts 
                GROUP BY vehicle_id 
                ORDER BY alert_count DESC 
                LIMIT 5
            """)
            
            # Esperar todas
            total_vehicles, total_rules, total_alerts, alerts_with_signal, top_offenders = await asyncio.gather(
                total_vehicles_task, total_rules_task, total_alerts_task, 
                alerts_with_signal_task, top_offenders_task
            )
        
        # ✅ REDIS INFO (con timeout)
        redis_memory = "N/A"
        if state.redis_enabled:
            try:
                redis_info = await asyncio.wait_for(
                    state.redis.info('memory'),
                    timeout=0.5
                )
                redis_memory = redis_info.get('used_memory_human', 'N/A')
            except:
                redis_memory = "timeout"
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "timestamp": datetime.now().isoformat(),
            "processing_time_ms": round(processing_time, 2),
            "database": {
                "active_vehicles": total_vehicles or 0,
                "active_rules": total_rules or 0,
                "total_alerts": total_alerts or 0,
                "alerts_with_signal_id": alerts_with_signal or 0,
                "signal_coverage": f"{round(alerts_with_signal/total_alerts*100, 1)}%" if total_alerts and total_alerts > 0 else "0%"
            },
            "top_offenders": [
                {"vehicle_id": row["vehicle_id"], "alerts": row["alert_count"]}
                for row in top_offenders
            ] if top_offenders else [],
            "redis": {
                "memory_used": redis_memory,
                "enabled": state.redis_enabled
            },
            "performance": {
                "pool_size": "100",
                "timeouts": "aggressive"
            }
        }
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- NUEVO ENDPOINT: RESET CIRCUIT BREAKER ---
@app.post("/redis/enable")
async def enable_redis():
    state.redis_enabled = True
    return {"status": "success", "message": "Redis re-enablado"}

@app.post("/redis/disable")
async def disable_redis():
    state.redis_enabled = False
    return {"status": "success", "message": "Redis deshabilitado"}

# --- METRICS ENDPOINT PARA MONITOREO ---
@app.get("/metrics")
async def get_metrics():
    """Endpoint para sistemas de monitoreo (Prometheus style)"""
    try:
        async with state.pool.acquire() as conn:
            active_connections = await conn.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
            )
            
            # Señales por minuto
            signals_per_min = await conn.fetchval("""
                SELECT COUNT(*) FROM signals 
                WHERE timestamp > NOW() - INTERVAL '1 minute'
            """)
            
            # Alertas por minuto
            alerts_per_min = await conn.fetchval("""
                SELECT COUNT(*) FROM alerts 
                WHERE timestamp > NOW() - INTERVAL '1 minute'
            """)
        
        return {
            "ccs_connections_active": active_connections or 0,
            "ccs_signals_per_minute": signals_per_min or 0,
            "ccs_alerts_per_minute": alerts_per_min or 0,
            "ccs_redis_enabled": 1 if state.redis_enabled else 0,
            "ccs_uptime_seconds": (datetime.now() - app_start_time).total_seconds() if 'app_start_time' in globals() else 0
        }
    except:
        return {"error": "metrics_unavailable"}

# Variable global para uptime
app_start_time = datetime.now()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="warning",  # Menos logs para más rendimiento
        limit_concurrency=1000,  # Más concurrencia
        timeout_keep_alive=30
    )