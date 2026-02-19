"""
domain/models.py - Modelos de datos y enums para CCS
"""

import json
import math
from datetime import datetime, time
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field, validator, confloat, constr


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