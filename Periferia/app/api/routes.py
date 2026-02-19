"""
api/routes.py - Endpoints de la API CCS
"""

import json
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, status, Body

from infrastructure.state import state
from domain.models import (
    Signal, RuleUpdate, GeofenceDefinition, ScheduleDefinition,
    HealthResponse, SignalResponse
)


def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
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
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Registrar endpoints
    app.post("/signal", response_model=SignalResponse, status_code=status.HTTP_202_ACCEPTED,
             tags=["signals"])(process_signal)
    app.post("/geofence", status_code=status.HTTP_201_CREATED,
             tags=["geofences"])(define_geofence)
    app.post("/schedule", status_code=status.HTTP_201_CREATED,
             tags=["schedules"])(define_schedule)
    app.post("/update-rule", tags=["rules"])(update_rule)
    app.get("/health", response_model=HealthResponse,
            tags=["monitoring"])(health_check)
    app.get("/metrics", tags=["monitoring"])(get_metrics)
    
    return app


# ============================================================================
# ENDPOINTS
# ============================================================================

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
            stream_name = state.EMERGENCY_STREAM_NAME
            priority = "emergency"
        else:
            # Stream normal
            stream_name = state.REDIS_STREAM_NAME
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor: {str(e)}"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error definiendo geocerca: {str(e)}"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error definiendo horario: {str(e)}"
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error actualizando regla: {str(e)}"
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
        stream_info = await state.redis.xinfo_stream(state.REDIS_STREAM_NAME)
        stream_normal_status = "healthy"
    except:
        stream_normal_status = "unhealthy"
    
    try:
        stream_info = await state.redis.xinfo_stream(state.EMERGENCY_STREAM_NAME)
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
                "normal_pending": await state.redis.xpending(state.REDIS_STREAM_NAME, "ccs_workers") if state.redis_enabled else 0,
                "emergency_pending": await state.redis.xpending(state.EMERGENCY_STREAM_NAME, "ccs_emergency_workers") if state.redis_enabled else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo métricas: {str(e)}"
        )