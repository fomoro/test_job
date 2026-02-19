"""
tests/unit/test_rule_service.py - Tests unitarios para RuleService

Responsabilidades:
- Testear la lógica de evaluación de reglas complejas
- Verificar cálculos de geocercas, horarios, detenciones
- Usar mocks para dependencias externas (DB, Redis)

Características:
- @pytest.mark.unit: Tests rápidos, sin dependencias reales
- Mocks de pool, redis, y caches
- Tests aislados de infraestructura
"""

import pytest
import asyncio
from datetime import datetime, time
from unittest.mock import AsyncMock, Mock, patch
import math

from domain.models import Signal, VehicleType, RuleType, ActionType
from application.services import RuleService


# ============================================================================
# FIXTURES PARA TESTS DE REGLAS
# ============================================================================

@pytest.fixture
def mock_pool():
    """Mock de asyncpg.Pool para tests."""
    pool = AsyncMock()
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    pool.acquire = AsyncMock(return_value=conn.__aenter__())
    return pool

@pytest.fixture
def sample_signal():
    """Señal de prueba básica."""
    return Signal(
        vehicle_id="TRUCK-001",
        speed=75.5,
        latitude=4.60971,
        longitude=-74.08175,
        timestamp=datetime(2024, 1, 15, 10, 30, 0),
        panic_button=False,
        temperature=None,
        vehicle_type=VehicleType.TRUCK,
        metadata={}
    )

@pytest.fixture
def sample_emergency_signal():
    """Señal de emergencia (botón pánico)."""
    return Signal(
        vehicle_id="TAXI-101",
        speed=0.0,
        latitude=4.60971,
        longitude=-74.08175,
        timestamp=datetime.utcnow(),
        panic_button=True,  # EMERGENCIA
        temperature=None,
        vehicle_type=VehicleType.CAR,
        metadata={}
    )

@pytest.fixture
def sample_rules():
    """Reglas de prueba."""
    return [
        {
            "id": 1,
            "rule_type": "MAX_SPEED",
            "comparison_value": "80.0",
            "action_type": "NOTIFY_OWNER",
            "priority": 1
        },
        {
            "id": 2,
            "rule_type": "PANIC_BUTTON",
            "comparison_value": "TRUE",
            "action_type": "NOTIFY_POLICE",
            "priority": 10
        },
        {
            "id": 3,
            "rule_type": "MAX_TEMP",
            "comparison_value": "-18.0",
            "action_type": "NOTIFY_OWNER",
            "priority": 5
        }
    ]

@pytest.fixture
def sample_geofence_cache():
    """Cache de geocercas de prueba."""
    return {
        "TRUCK-001": [
            {
                "name": "ZONA_NORTE",
                "center": {"latitude": 4.60971, "longitude": -74.08175},
                "radius_km": 5.0,
                "is_allowed": True
            }
        ]
    }

@pytest.fixture
def sample_schedule_cache():
    """Cache de horarios de prueba."""
    return {
        "MOTO-301": {
            "start_time": "06:00",
            "end_time": "22:00",
            "days_of_week": [1, 2, 3, 4, 5]  # Lunes a Viernes
        }
    }


# ============================================================================
# TESTS PARA EVALUACIÓN DE REGLAS COMPLEJAS
# ============================================================================

class TestRuleServiceEvaluateComplexRules:
    """Tests para evaluate_complex_rules()."""
    
    @pytest.mark.asyncio
    async def test_no_violations_returns_empty_list(
        self, sample_signal, mock_pool, sample_rules, 
        sample_geofence_cache, sample_schedule_cache
    ):
        """Cuando no hay violaciones, retorna lista vacía."""
        # Señal que NO viola reglas
        signal = sample_signal
        signal.speed = 70.0  # Menor a 80.0
        signal.panic_button = False
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[sample_rules[0]],  # Solo regla de velocidad
            geofence_cache={},  # Sin geocercas
            schedule_cache={},  # Sin horarios
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert alerts == []
    
    @pytest.mark.asyncio
    async def test_speed_violation_detected(
        self, sample_signal, mock_pool, sample_rules
    ):
        """Detectar exceso de velocidad."""
        # Señal que SÍ viola velocidad
        signal = sample_signal
        signal.speed = 90.0  # Mayor a 80.0
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[sample_rules[0]],  # Regla MAX_SPEED: 80.0
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert len(alerts) == 1
        alert_tuple = alerts[0]
        
        # Verificar estructura de la alerta
        assert alert_tuple[0] == "TRUCK-001"  # vehicle_id
        assert alert_tuple[1] == 1  # rule_id
        assert alert_tuple[2] == 123  # signal_id
        assert "Exceso velocidad" in alert_tuple[3]  # message
        assert alert_tuple[4] == "NOTIFY_OWNER"  # action_type
    
    @pytest.mark.asyncio
    async def test_panic_button_violation_detected(
        self, sample_emergency_signal, mock_pool, sample_rules
    ):
        """Detectar botón de pánico activado."""
        alerts = await RuleService.evaluate_complex_rules(
            signal=sample_emergency_signal,
            signal_id=456,
            reglas=[sample_rules[1]],  # Regla PANIC_BUTTON
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert len(alerts) == 1
        assert "BOTÓN DE PÁNICO" in alerts[0][3]
        assert alerts[0][4] == "NOTIFY_POLICE"
    
    @pytest.mark.asyncio
    async def test_temperature_violation_detected(
        self, sample_signal, mock_pool, sample_rules
    ):
        """Detectar temperatura fuera de rango."""
        signal = sample_signal
        signal.temperature = -20.0  # Menor a -18.0 (MAX_TEMP es -18.0?)
        # Nota: En sample_rules[2] es MAX_TEMP: -18.0, pero es confuso
        # Para este test, cambiamos a MIN_TEMP
        
        # Crear regla de temperatura mínima
        temp_rule = {
            "id": 3,
            "rule_type": "MIN_TEMP",
            "comparison_value": "-15.0",
            "action_type": "NOTIFY_OWNER",
            "priority": 5
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=789,
            reglas=[temp_rule],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert len(alerts) == 1
        assert "Temperatura BAJA" in alerts[0][3]
    
    @pytest.mark.asyncio
    async def test_multiple_violations_same_signal(
        self, sample_signal, mock_pool
    ):
        """Múltiples violaciones en una misma señal."""
        signal = sample_signal
        signal.speed = 90.0  # Violación velocidad
        signal.panic_button = True  # Violación pánico
        signal.metadata["door_status"] = "open"  # Violación puerta
        
        rules = [
            {
                "id": 1,
                "rule_type": "MAX_SPEED",
                "comparison_value": "80.0",
                "action_type": "NOTIFY_OWNER",
                "priority": 1
            },
            {
                "id": 2,
                "rule_type": "PANIC_BUTTON",
                "comparison_value": "TRUE",
                "action_type": "NOTIFY_POLICE",
                "priority": 10
            },
            {
                "id": 3,
                "rule_type": "DOOR_SENSOR",
                "comparison_value": "OPEN",
                "action_type": "LOG_ONLY",
                "priority": 2
            }
        ]
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=999,
            reglas=rules,
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        # Debería tener 3 alertas (velocidad, pánico, puerta)
        assert len(alerts) == 3
        
        # Verificar que cada tipo de alerta está presente
        alert_messages = [alert[3] for alert in alerts]
        assert any("Exceso velocidad" in msg for msg in alert_messages)
        assert any("BOTÓN DE PÁNICO" in msg for msg in alert_messages)
        assert any("Puerta abierta" in msg for msg in alert_messages)
    
    @pytest.mark.asyncio
    async def test_metrics_updated_on_alerts(self, sample_signal, mock_pool):
        """Verificar que las métricas se actualizan con alertas."""
        signal = sample_signal
        signal.speed = 90.0  # Violación
        
        metrics = {"alerts_generated": 0}
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[{
                "id": 1,
                "rule_type": "MAX_SPEED",
                "comparison_value": "80.0",
                "action_type": "NOTIFY_OWNER",
                "priority": 1
            }],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics=metrics
        )
        
        assert len(alerts) == 1
        assert metrics["alerts_generated"] == 1


# ============================================================================
# TESTS PARA REGLAS DE GEOFENCE
# ============================================================================

class TestGeofenceRules:
    """Tests específicos para reglas de geocercas."""
    
    @pytest.mark.asyncio
    async def test_geofence_exit_violation_detected(
        self, sample_signal, mock_pool
    ):
        """Detectar salida de geocerca permitida."""
        signal = sample_signal
        # Posición FUERA de la geocerca (más de 5km del centro)
        signal.latitude = 4.70000
        signal.longitude = -74.20000
        
        geofence_cache = {
            "TRUCK-001": [
                {
                    "name": "ZONA_NORTE",
                    "center": {"latitude": 4.60971, "longitude": -74.08175},
                    "radius_km": 5.0,
                    "is_allowed": True
                }
            ]
        }
        
        rule = {
            "id": 10,
            "rule_type": "GEOFENCE_EXIT",
            "comparison_value": "ZONA_NORTE",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache=geofence_cache,
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert len(alerts) == 1
        assert "Salida de zona" in alerts[0][3]
        assert "ZONA_NORTE" in alerts[0][3]
    
    @pytest.mark.asyncio
    async def test_geofence_exit_no_violation_when_inside(
        self, sample_signal, mock_pool
    ):
        """NO detectar violación cuando está dentro de la geocerca."""
        signal = sample_signal
        # Posición DENTRO de la geocerca (menos de 5km del centro)
        signal.latitude = 4.61000  # Muy cerca del centro
        signal.longitude = -74.08200
        
        geofence_cache = {
            "TRUCK-001": [
                {
                    "name": "ZONA_NORTE",
                    "center": {"latitude": 4.60971, "longitude": -74.08175},
                    "radius_km": 5.0,
                    "is_allowed": True
                }
            ]
        }
        
        rule = {
            "id": 10,
            "rule_type": "GEOFENCE_EXIT",
            "comparison_value": "ZONA_NORTE",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache=geofence_cache,
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert alerts == []  # No debería haber alertas
    
    @pytest.mark.asyncio
    async def test_geofence_exit_ignored_if_not_allowed_zone(
        self, sample_signal, mock_pool
    ):
        """Ignorar salida si la zona no es allowed (es prohibida)."""
        signal = sample_signal
        signal.latitude = 4.70000  # Fuera de la zona
        signal.longitude = -74.20000
        
        # Zona PROHIBIDA (is_allowed=False)
        geofence_cache = {
            "TRUCK-001": [
                {
                    "name": "ZONA_PROHIBIDA",
                    "center": {"latitude": 4.60971, "longitude": -74.08175},
                    "radius_km": 5.0,
                    "is_allowed": False  # ¡Zona prohibida!
                }
            ]
        }
        
        rule = {
            "id": 10,
            "rule_type": "GEOFENCE_EXIT",
            "comparison_value": "ZONA_PROHIBIDA",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache=geofence_cache,
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        # No debería alertar por salir de zona prohibida
        # (solo alerta por entrar a zona prohibida, pero esa regla no está implementada)
        assert alerts == []
    
    @pytest.mark.asyncio
    async def test_geofence_no_cache_for_vehicle(self, sample_signal, mock_pool):
        """Manejar caso cuando vehículo no tiene geocercas en cache."""
        rule = {
            "id": 10,
            "rule_type": "GEOFENCE_EXIT",
            "comparison_value": "ZONA_NORTE",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=sample_signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},  # Cache vacío
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert alerts == []  # Sin cache, no hay violación


# ============================================================================
# TESTS PARA REGLAS DE HORARIO (SCHEDULE)
# ============================================================================

class TestScheduleRules:
    """Tests específicos para reglas de horario."""
    
    @pytest.mark.asyncio
    async def test_schedule_violation_outside_hours(
        self, sample_signal, mock_pool
    ):
        """Detectar movimiento fuera de horario permitido."""
        signal = sample_signal
        signal.vehicle_id = "MOTO-301"
        # Lunes (día 1) a las 23:00 (fuera de 06:00-22:00)
        signal.timestamp = datetime(2024, 1, 1, 23, 0, 0)  # Lunes
        
        schedule_cache = {
            "MOTO-301": {
                "start_time": "06:00",
                "end_time": "22:00",
                "days_of_week": [1, 2, 3, 4, 5]  # Lunes a Viernes
            }
        }
        
        rule = {
            "id": 20,
            "rule_type": "SCHEDULE",
            "comparison_value": "ANY",  # Valor no usado realmente
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache=schedule_cache,
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert len(alerts) == 1
        assert "Movimiento en horario no permitido" in alerts[0][3]
    
    @pytest.mark.asyncio
    async def test_schedule_no_violation_during_allowed_hours(
        self, sample_signal, mock_pool
    ):
        """NO detectar violación durante horario permitido."""
        signal = sample_signal
        signal.vehicle_id = "MOTO-301"
        # Lunes (día 1) a las 14:00 (dentro de 06:00-22:00)
        signal.timestamp = datetime(2024, 1, 1, 14, 0, 0)  # Lunes
        
        schedule_cache = {
            "MOTO-301": {
                "start_time": "06:00",
                "end_time": "22:00",
                "days_of_week": [1, 2, 3, 4, 5]
            }
        }
        
        rule = {
            "id": 20,
            "rule_type": "SCHEDULE",
            "comparison_value": "ANY",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache=schedule_cache,
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert alerts == []  # No debería haber alertas
    
    @pytest.mark.asyncio
    async def test_schedule_violation_wrong_day(
        self, sample_signal, mock_pool
    ):
        """Detectar movimiento en día no permitido."""
        signal = sample_signal
        signal.vehicle_id = "MOTO-301"
        # Sábado (día 6) - no permitido (solo Lunes-Viernes)
        signal.timestamp = datetime(2024, 1, 6, 10, 0, 0)  # Sábado
        
        schedule_cache = {
            "MOTO-301": {
                "start_time": "06:00",
                "end_time": "22:00",
                "days_of_week": [1, 2, 3, 4, 5]  # Solo días de semana
            }
        }
        
        rule = {
            "id": 20,
            "rule_type": "SCHEDULE",
            "comparison_value": "ANY",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache=schedule_cache,
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert len(alerts) == 1
        assert "Movimiento en horario no permitido" in alerts[0][3]
    
    @pytest.mark.asyncio
    async def test_schedule_crossing_midnight_allowed(
        self, sample_signal, mock_pool
    ):
        """Horario que cruza medianoche (ej: 22:00-06:00)."""
        signal = sample_signal
        signal.vehicle_id = "NIGHT-001"
        # Viernes a las 23:00 - DENTRO de horario 22:00-06:00
        signal.timestamp = datetime(2024, 1, 5, 23, 0, 0)  # Viernes
        
        schedule_cache = {
            "NIGHT-001": {
                "start_time": "22:00",
                "end_time": "06:00",  # Cruza medianoche
                "days_of_week": [1, 2, 3, 4, 5]
            }
        }
        
        rule = {
            "id": 20,
            "rule_type": "SCHEDULE",
            "comparison_value": "ANY",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache=schedule_cache,
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert alerts == []  # Dentro de horario (22:00-06:00 incluye 23:00)


# ============================================================================
# TESTS PARA REGLAS DE DETENCIÓN NO PLANEADA
# ============================================================================

class TestUnplannedStopRules:
    """Tests para detección de detenciones no planeadas."""
    
    @pytest.mark.asyncio
    async def test_unplanned_stop_detection(
        self, sample_signal, mock_pool
    ):
        """Detectar detención no planeada."""
        signal = sample_signal
        signal.speed = 0.0  # Detenido
        
        # Mockear la consulta a la base de datos
        mock_conn = AsyncMock()
        
        # Simular que había movimiento recientemente y ahora está detenido
        mock_conn.fetch.return_value = [
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 30, 0)},  # Última
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 29, 50)},  # 2da
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 29, 40)},  # 3ra
            {"speed": 60.0, "timestamp": datetime(2024, 1, 15, 10, 29, 0)},  # 4ta - movimiento
            {"speed": 55.0, "timestamp": datetime(2024, 1, 15, 10, 28, 50)},  # 5ta - movimiento
        ]
        
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rule = {
            "id": 30,
            "rule_type": "UNPLANNED_STOP",
            "comparison_value": "TRUE",
            "action_type": "NOTIFY_OWNER",
            "priority": 3
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        # Debería detectar detención no planeada
        # (últimas 3 señales detenidas, pero había movimiento antes)
        assert len(alerts) == 1
        assert "Detención no planeada" in alerts[0][3]
    
    @pytest.mark.asyncio
    async def test_no_unplanned_stop_when_always_stopped(
        self, sample_signal, mock_pool
    ):
        """NO detectar si siempre estuvo detenido."""
        signal = sample_signal
        signal.speed = 0.0
        
        mock_conn = AsyncMock()
        # Todas las señales muestran detención
        mock_conn.fetch.return_value = [
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 30, 0)},
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 29, 50)},
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 29, 40)},
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 29, 0)},
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 28, 50)},
        ]
        
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rule = {
            "id": 30,
            "rule_type": "UNPLANNED_STOP",
            "comparison_value": "TRUE",
            "action_type": "NOTIFY_OWNER",
            "priority": 3
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        # No debería alertar - siempre estuvo detenido
        assert alerts == []
    
    @pytest.mark.asyncio
    async def test_unplanned_stop_insufficient_data(
        self, sample_signal, mock_pool
    ):
        """NO detectar si no hay suficientes datos históricos."""
        signal = sample_signal
        signal.speed = 0.0
        
        mock_conn = AsyncMock()
        # Solo 2 señales históricas (se necesitan al menos 3)
        mock_conn.fetch.return_value = [
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 30, 0)},
            {"speed": 0.0, "timestamp": datetime(2024, 1, 15, 10, 29, 50)},
        ]
        
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rule = {
            "id": 30,
            "rule_type": "UNPLANNED_STOP",
            "comparison_value": "TRUE",
            "action_type": "NOTIFY_OWNER",
            "priority": 3
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        # No hay suficientes datos para determinar
        assert alerts == []


# ============================================================================
# TESTS PARA REGLAS DE SENSOR DE PUERTA
# ============================================================================

class TestDoorSensorRules:
    """Tests para reglas de sensor de puerta."""
    
    @pytest.mark.asyncio
    async def test_door_open_during_movement_violation(
        self, sample_signal, mock_pool
    ):
        """Detectar puerta abierta durante movimiento."""
        signal = sample_signal
        signal.speed = 50.0  # En movimiento
        signal.metadata["door_status"] = "open"  # Puerta abierta
        
        rule = {
            "id": 40,
            "rule_type": "DOOR_SENSOR",
            "comparison_value": "OPEN",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert len(alerts) == 1
        assert "Puerta abierta durante movimiento" in alerts[0][3]
    
    @pytest.mark.asyncio
    async def test_door_open_when_stopped_no_violation(
        self, sample_signal, mock_pool
    ):
        """NO detectar violación si puerta abierta pero detenido."""
        signal = sample_signal
        signal.speed = 0.0  # Detenido
        signal.metadata["door_status"] = "open"  # Puerta abierta
        
        rule = {
            "id": 40,
            "rule_type": "DOOR_SENSOR",
            "comparison_value": "OPEN",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        # Puerta abierta cuando detenido está permitido
        assert alerts == []
    
    @pytest.mark.asyncio
    async def test_door_closed_no_violation(
        self, sample_signal, mock_pool
    ):
        """NO detectar violación si puerta cerrada."""
        signal = sample_signal
        signal.speed = 50.0  # En movimiento
        signal.metadata["door_status"] = "closed"  # Puerta cerrada
        
        rule = {
            "id": 40,
            "rule_type": "DOOR_SENSOR",
            "comparison_value": "OPEN",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        assert alerts == []  # Puerta cerrada, no hay violación


# ============================================================================
# TESTS PARA CÁLCULO DE DISTANCIA (Haversine)
# ============================================================================

class TestDistanceCalculation:
    """Tests para el cálculo de distancia entre coordenadas."""
    
    def test_calculate_distance_same_point(self):
        """Distancia entre el mismo punto debe ser 0."""
        distance = RuleService._calculate_distance(
            lat1=4.60971, lon1=-74.08175,
            lat2=4.60971, lon2=-74.08175
        )
        
        assert distance == 0.0
    
    def test_calculate_distance_known_distance(self):
        """Verificar cálculo con distancia conocida."""
        # Bogotá (4.60971, -74.08175) a Medellín (6.24474, -75.57482)
        # Distancia aproximada: ~240km
        distance = RuleService._calculate_distance(
            lat1=4.60971, lon1=-74.08175,  # Bogotá
            lat2=6.24474, lon2=-75.57482   # Medellín
        )
        
        # La distancia real es ~240km, aceptamos margen de error
        assert 230 <= distance <= 250
        assert isinstance(distance, float)
    
    def test_calculate_distance_opposite_side_of_earth(self):
        """Distancia entre puntos opuestos de la Tierra."""
        # Punto opuesto aproximado
        distance = RuleService._calculate_distance(
            lat1=0.0, lon1=0.0,
            lat2=0.0, lon2=180.0
        )
        
        # Mitad de la circunferencia de la Tierra
        expected = math.pi * 6371.0  # π * radio_tierra
        assert abs(distance - expected) < 10  # Margen de error
    
    def test_calculate_distance_with_negative_coordinates(self):
        """Distancia con coordenadas negativas."""
        distance = RuleService._calculate_distance(
            lat1=-34.60372, lon1=-58.38159,  # Buenos Aires
            lat2=40.71278, lon2=-74.00594    # Nueva York
        )
        
        # Distancia aproximada conocida
        assert 8000 <= distance <= 9000  # ~8500km


# ============================================================================
# TESTS PARA MÉTODOS PRIVADOS DE VALIDACIÓN
# ============================================================================

class TestPrivateValidationMethods:
    """Tests para métodos privados de validación."""
    
    @pytest.mark.asyncio
    async def test_check_geofence_violation_outside_zone(self):
        """Verificar que detecta fuera de zona."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=4.70000,  # Fuera de zona
            longitude=-74.20000,
            timestamp=datetime.utcnow()
        )
        
        geofences = [
            {
                "name": "ZONA_NORTE",
                "center": {"latitude": 4.60971, "longitude": -74.08175},
                "radius_km": 5.0,
                "is_allowed": True
            }
        ]
        
        violation = await RuleService._check_geofence_violation(
            signal=signal,
            geofences=geofences,
            zone_name="ZONA_NORTE"
        )
        
        assert violation is True
    
    @pytest.mark.asyncio
    async def test_check_geofence_violation_inside_zone(self):
        """Verificar que NO detecta cuando está dentro de zona."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=4.61000,  # Dentro de zona (cerca del centro)
            longitude=-74.08200,
            timestamp=datetime.utcnow()
        )
        
        geofences = [
            {
                "name": "ZONA_NORTE",
                "center": {"latitude": 4.60971, "longitude": -74.08175},
                "radius_km": 5.0,
                "is_allowed": True
            }
        ]
        
        violation = await RuleService._check_geofence_violation(
            signal=signal,
            geofences=geofences,
            zone_name="ZONA_NORTE"
        )
        
        assert violation is False
    
    @pytest.mark.asyncio
    async def test_check_schedule_violation_outside_hours(self):
        """Verificar violación fuera de horario."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0,
            timestamp=datetime(2024, 1, 15, 23, 0, 0)  # 23:00
        )
        
        schedule = {
            "start_time": "06:00",
            "end_time": "22:00",
            "days_of_week": [1, 2, 3, 4, 5, 6, 7]
        }
        
        violation = await RuleService._check_schedule_violation(
            signal=signal,
            schedule=schedule
        )
        
        assert violation is True
    
    @pytest.mark.asyncio
    async def test_check_schedule_violation_wrong_day(self):
        """Verificar violación en día no permitido."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0,
            timestamp=datetime(2024, 1, 6, 10, 0, 0)  # Sábado (día 6)
        )
        
        schedule = {
            "start_time": "06:00",
            "end_time": "22:00",
            "days_of_week": [1, 2, 3, 4, 5]  # Solo días de semana
        }
        
        violation = await RuleService._check_schedule_violation(
            signal=signal,
            schedule=schedule
        )
        
        assert violation is True
    
    @pytest.mark.asyncio
    async def test_check_schedule_no_violation_during_allowed_time(self):
        """NO violación durante horario permitido."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0,
            timestamp=datetime(2024, 1, 1, 14, 0, 0)  # Lunes 14:00
        )
        
        schedule = {
            "start_time": "06:00",
            "end_time": "22:00",
            "days_of_week": [1, 2, 3, 4, 5, 6, 7]
        }
        
        violation = await RuleService._check_schedule_violation(
            signal=signal,
            schedule=schedule
        )
        
        assert violation is False


# ============================================================================
# TESTS PARA ERROR HANDLING
# ============================================================================

class TestErrorHandling:
    """Tests para manejo de errores en RuleService."""
    
    @pytest.mark.asyncio
    async def test_geofence_violation_with_invalid_geofence_data(self):
        """Manejar datos inválidos en geocercas."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0,
            timestamp=datetime.utcnow()
        )
        
        # Geocerca con datos inválidos (sin centro)
        geofences = [
            {
                "name": "INVALID_ZONE",
                "center": {},  # Centro vacío
                "radius_km": 5.0,
                "is_allowed": True
            }
        ]
        
        # No debería lanzar excepción, solo retornar False
        violation = await RuleService._check_geofence_violation(
            signal=signal,
            geofences=geofences,
            zone_name="INVALID_ZONE"
        )
        
        assert violation is False
    
    @pytest.mark.asyncio
    async def test_schedule_violation_with_invalid_schedule_data(self):
        """Manejar datos inválidos en horarios."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0,
            timestamp=datetime.utcnow()
        )
        
        # Horario con datos inválidos
        schedule = {
            "start_time": "invalid-time",
            "end_time": "22:00",
            "days_of_week": [1, 2, 3]
        }
        
        # Debería manejar el error y retornar False
        violation = await RuleService._check_schedule_violation(
            signal=signal,
            schedule=schedule
        )
        
        # En caso de error, asumimos no violación
        assert violation is False
    
    @pytest.mark.asyncio
    async def test_unplanned_stop_with_db_error(self, sample_signal, mock_pool):
        """Manejar error de base de datos en detección de detención."""
        signal = sample_signal
        signal.speed = 0.0
        
        # Simular error en la consulta
        mock_conn = AsyncMock()
        mock_conn.fetch.side_effect = Exception("Error de conexión a DB")
        
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rule = {
            "id": 30,
            "rule_type": "UNPLANNED_STOP",
            "comparison_value": "TRUE",
            "action_type": "NOTIFY_OWNER",
            "priority": 3
        }
        
        alerts = await RuleService.evaluate_complex_rules(
            signal=signal,
            signal_id=123,
            reglas=[rule],
            geofence_cache={},
            schedule_cache={},
            pool=mock_pool,
            redis_enabled=True,
            metrics={}
        )
        
        # En caso de error, no debería generar alerta
        assert alerts == []