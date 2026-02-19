"""
tests/integration/test_routes.py - Tests de integración para endpoints API

Responsabilidades:
- Testear endpoints HTTP reales con TestClient
- Verificar respuestas HTTP, códigos de estado, schemas
- Integración con estado global (GlobalState) mockeado
- Simular escenarios reales de uso

Características:
- @pytest.mark.integration: Tests que prueban integración de componentes
- @pytest.mark.slow: Pueden ser más lentos por usar TestClient
- Mocks estratégicos de componentes externos (DB, Redis)
- Verificación de flujos completos de API
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
import pytest
from fastapi.testclient import TestClient

from domain.models import Signal, VehicleType, RuleType, ActionType


# ============================================================================
# FIXTURES PARA TESTS DE RUTAS
# ============================================================================

@pytest.fixture
def test_client():
    """TestClient de FastAPI con app configurada para testing."""
    # Necesitamos patch para evitar inicialización real de GlobalState
    with patch('infrastructure.state.GlobalState'):
        from main import app
        return TestClient(app)

@pytest.fixture
def mock_state():
    """Mock completo de GlobalState para tests."""
    state = Mock()
    
    # Configurar atributos básicos
    state.redis_enabled = True
    state.api_instance_id = "test-api-12345"
    state.start_time = datetime.utcnow()
    state.metrics = {
        "signals_processed": 0,
        "alerts_generated": 0,
        "emergencies_processed": 0,
        "last_emergency_time": None
    }
    
    # Configurar Redis mock
    state.redis = AsyncMock()
    state.redis.xadd = AsyncMock(return_value="1705311000000-0")
    state.redis.ping = AsyncMock(return_value=True)
    state.redis.xinfo_stream = AsyncMock(return_value={"length": 0})
    state.redis.xpending = AsyncMock(return_value={"pending": 0})
    state.redis.info = AsyncMock(return_value={"connected_clients": 1})
    
    # Configurar PostgreSQL pool mock
    state.pool = AsyncMock()
    mock_conn = AsyncMock()
    mock_conn.fetchval = AsyncMock(return_value=1)
    mock_conn.execute = AsyncMock(return_value="UPDATE 1")
    mock_conn.fetch = AsyncMock(return_value=[])
    mock_conn.fetchrow = AsyncMock(return_value=None)
    state.pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
    
    # Configurar streams
    state.REDIS_STREAM_NAME = "ccs_signals_stream"
    state.EMERGENCY_STREAM_NAME = "ccs_emergency_stream"
    
    return state

@pytest.fixture
def sample_signal_data():
    """Datos de señal para tests."""
    return {
        "vehicle_id": "TRUCK-001",
        "speed": 75.5,
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
    }

@pytest.fixture
def sample_emergency_signal_data():
    """Datos de señal de emergencia."""
    return {
        "vehicle_id": "TAXI-101",
        "speed": 0.0,
        "latitude": 4.60971,
        "longitude": -74.08175,
        "timestamp": "2024-01-15T10:30:00Z",
        "panic_button": True,  # ¡EMERGENCIA!
        "temperature": None,
        "vehicle_type": "CAR",
        "metadata": {}
    }


# ============================================================================
# TESTS PARA ENDPOINT /health
# ============================================================================

class TestHealthEndpoint:
    """Tests para GET /health."""
    
    @pytest.mark.integration
    def test_health_check_success(self, test_client, mock_state):
        """Verificar que /health responde correctamente cuando todo está bien."""
        # Patch state en el módulo de rutas
        with patch('api.routes.state', mock_state):
            response = test_client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert "services" in data
            assert "postgresql" in data["services"]
            assert "redis" in data["services"]
            assert "timestamp" in data
            assert "uptime_seconds" in data
    
    @pytest.mark.integration
    def test_health_check_with_unhealthy_redis(self, test_client, mock_state):
        """/health debe mostrar redis como unhealthy cuando falla."""
        # Configurar Redis para fallar
        mock_state.redis.ping = AsyncMock(side_effect=Exception("Redis down"))
        
        with patch('api.routes.state', mock_state):
            response = test_client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["services"]["redis"] == "unhealthy"
            assert data["status"] in ["degraded", "unhealthy"]
    
    @pytest.mark.integration
    def test_health_check_with_unhealthy_postgresql(self, test_client, mock_state):
        """/health debe mostrar postgresql como unhealthy cuando falla."""
        # Configurar PostgreSQL para fallar
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("DB down"))
        mock_state.pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        with patch('api.routes.state', mock_state):
            response = test_client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["services"]["postgresql"] == "unhealthy"
    
    @pytest.mark.integration
    def test_health_check_with_redis_disabled(self, test_client, mock_state):
        """/health debe manejar cuando redis está deshabilitado."""
        mock_state.redis_enabled = False
        
        with patch('api.routes.state', mock_state):
            response = test_client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["services"]["redis"] == "circuit_open"
    
    @pytest.mark.integration
    def test_health_check_includes_metrics(self, test_client, mock_state):
        """/health debe incluir métricas cuando están disponibles."""
        mock_state.metrics = {
            "signals_processed": 1500,
            "alerts_generated": 45,
            "emergencies_processed": 3,
            "last_emergency_time": "2024-01-15T10:25:00Z"
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.get("/health")
            
            data = response.json()
            assert "metrics" in data
            assert data["metrics"]["signals_processed"] == 1500
            assert data["metrics"]["alerts_generated"] == 45


# ============================================================================
# TESTS PARA ENDPOINT /signal
# ============================================================================

class TestSignalEndpoint:
    """Tests para POST /signal."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_signal_success(self, test_client, mock_state, sample_signal_data):
        """Procesar señal normal exitosamente."""
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/signal",
                json=sample_signal_data
            )
            
            assert response.status_code == 202  # Accepted
            
            data = response.json()
            assert data["status"] == "accepted"
            assert data["vehicle_id"] == "TRUCK-001"
            assert data["priority"] == "normal"
            assert "message_id" in data
            assert "processing_time_ms" in data
            assert "timestamp" in data
            
            # Verificar que se llamó a Redis con stream normal
            mock_state.redis.xadd.assert_called_once()
            call_args = mock_state.redis.xadd.call_args
            assert call_args[0][0] == mock_state.REDIS_STREAM_NAME
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_emergency_signal(self, test_client, mock_state, sample_emergency_signal_data):
        """Procesar señal de emergencia (debe usar stream de emergencia)."""
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/signal",
                json=sample_emergency_signal_data
            )
            
            assert response.status_code == 202
            
            data = response.json()
            assert data["priority"] == "emergency"
            assert data["vehicle_id"] == "TAXI-101"
            
            # Debería usar stream de emergencia
            mock_state.redis.xadd.assert_called_once()
            call_args = mock_state.redis.xadd.call_args
            assert call_args[0][0] == mock_state.EMERGENCY_STREAM_NAME
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_signal_with_redis_disabled(self, test_client, mock_state, sample_signal_data):
        """Error cuando Redis está deshabilitado."""
        mock_state.redis_enabled = False
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/signal",
                json=sample_signal_data
            )
            
            assert response.status_code == 503  # Service Unavailable
            assert "Redis deshabilitado" in response.json()["detail"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_signal_with_redis_error(self, test_client, mock_state, sample_signal_data):
        """Error cuando Redis falla al publicar."""
        mock_state.redis.xadd = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/signal",
                json=sample_signal_data
            )
            
            assert response.status_code == 500  # Internal Server Error
            assert "Error interno" in response.json()["detail"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_signal_invalid_data(self, test_client, mock_state):
        """Error cuando los datos de la señal son inválidos."""
        invalid_data = {
            "vehicle_id": "",  # Vacío (inválido)
            "speed": -10.0,    # Negativo (inválido)
            "latitude": 100.0, # Fuera de rango
            "longitude": 200.0 # Fuera de rango
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/signal",
                json=invalid_data
            )
            
            # Pydantic debería validar y retornar 422
            assert response.status_code == 422  # Unprocessable Entity
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_signal_with_minimal_data(self, test_client, mock_state):
        """Procesar señal con datos mínimos requeridos."""
        minimal_data = {
            "vehicle_id": "TEST-001",
            "speed": 50.0,
            "latitude": 0.0,
            "longitude": 0.0
            # timestamp auto-generado, otros campos opcionales
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/signal",
                json=minimal_data
            )
            
            assert response.status_code == 202
            assert response.json()["status"] == "accepted"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_process_signal_processing_time_measured(self, test_client, mock_state, sample_signal_data):
        """Verificar que se mide el tiempo de procesamiento."""
        import time
        
        with patch('api.routes.state', mock_state):
            start = time.time()
            response = test_client.post("/signal", json=sample_signal_data)
            end = time.time()
            
            assert response.status_code == 202
            
            data = response.json()
            processing_time = data["processing_time_ms"]
            
            # El tiempo medido debe ser razonable
            assert 0 <= processing_time <= (end - start) * 1000 + 100  # Margen


# ============================================================================
# TESTS PARA ENDPOINT /geofence
# ============================================================================

class TestGeofenceEndpoint:
    """Tests para POST /geofence."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_geofence_success(self, test_client, mock_state):
        """Definir geocerca exitosamente."""
        geofence_data = {
            "vehicle_id": "TRUCK-001",
            "geofence": {
                "name": "Zona_Norte_Bogota",
                "center": {
                    "latitude": 4.60971,
                    "longitude": -74.08175
                },
                "radius_km": 5.0,
                "is_allowed": True
            }
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/geofence",
                json=geofence_data
            )
            
            assert response.status_code == 201  # Created
            
            data = response.json()
            assert data["status"] == "created"
            assert data["vehicle_id"] == "TRUCK-001"
            assert "geofence_id" in data
            assert "Zona_Norte_Bogota" in data["message"]
            
            # Verificar que se actualizó el cache
            assert "TRUCK-001" in mock_state.geofence_cache
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_geofence_invalid_data(self, test_client, mock_state):
        """Error cuando los datos de la geocerca son inválidos."""
        invalid_data = {
            "vehicle_id": "TRUCK-001",
            "geofence": {
                "name": "",  # Nombre vacío
                "center": {
                    "latitude": 100.0,  # Fuera de rango
                    "longitude": 200.0
                },
                "radius_km": -5.0  # Radio negativo
            }
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/geofence",
                json=invalid_data
            )
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_geofence_db_error(self, test_client, mock_state):
        """Manejar error al actualizar la base de datos."""
        geofence_data = {
            "vehicle_id": "TRUCK-001",
            "geofence": {
                "name": "Test",
                "center": {"latitude": 0.0, "longitude": 0.0},
                "radius_km": 1.0
            }
        }
        
        # Configurar error en DB
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_state.pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/geofence",
                json=geofence_data
            )
            
            assert response.status_code == 500
            assert "Error definiendo geocerca" in response.json()["detail"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_multiple_geofences_same_vehicle(self, test_client, mock_state):
        """Definir múltiples geocercas para el mismo vehículo."""
        # Primera geocerca
        geofence1 = {
            "vehicle_id": "TRUCK-001",
            "geofence": {
                "name": "Zona_Norte",
                "center": {"latitude": 4.60971, "longitude": -74.08175},
                "radius_km": 5.0
            }
        }
        
        # Segunda geocerca
        geofence2 = {
            "vehicle_id": "TRUCK-001",
            "geofence": {
                "name": "Zona_Sur",
                "center": {"latitude": 4.50000, "longitude": -74.10000},
                "radius_km": 3.0
            }
        }
        
        with patch('api.routes.state', mock_state):
            # Primera geocerca
            response1 = test_client.post("/geofence", json=geofence1)
            assert response1.status_code == 201
            
            # Segunda geocerca
            response2 = test_client.post("/geofence", json=geofence2)
            assert response2.status_code == 201
            
            # Debería tener 2 geocercas en cache
            assert len(mock_state.geofence_cache.get("TRUCK-001", [])) == 2


# ============================================================================
# TESTS PARA ENDPOINT /schedule
# ============================================================================

class TestScheduleEndpoint:
    """Tests para POST /schedule."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_schedule_success(self, test_client, mock_state):
        """Definir horario exitosamente."""
        schedule_data = {
            "vehicle_id": "MOTO-301",
            "schedule": {
                "start_time": "06:00",
                "end_time": "22:00",
                "days_of_week": [1, 2, 3, 4, 5]  # Lunes a Viernes
            }
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/schedule",
                json=schedule_data
            )
            
            assert response.status_code == 201
            
            data = response.json()
            assert data["status"] == "created"
            assert data["vehicle_id"] == "MOTO-301"
            assert "schedule_id" in data
            assert "06:00-22:00" in data["message"]
            assert "Lunes" in data["message"]  # Días traducidos
            
            # Verificar que se actualizó el cache
            assert "MOTO-301" in mock_state.schedule_cache
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_schedule_with_default_days(self, test_client, mock_state):
        """Definir horario con días por defecto (todos los días)."""
        schedule_data = {
            "vehicle_id": "TRUCK-001",
            "schedule": {
                "start_time": "00:00",
                "end_time": "23:59"
                # days_of_week omitido, debe usar default
            }
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/schedule",
                json=schedule_data
            )
            
            assert response.status_code == 201
            
            # El horario en cache debería tener todos los días
            schedule = mock_state.schedule_cache.get("TRUCK-001")
            assert schedule["days_of_week"] == [1, 2, 3, 4, 5, 6, 7]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_schedule_invalid_time_format(self, test_client, mock_state):
        """Error cuando el formato de hora es inválido."""
        invalid_data = {
            "vehicle_id": "TEST-001",
            "schedule": {
                "start_time": "25:00",  # Hora inválida
                "end_time": "22:00"
            }
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/schedule",
                json=invalid_data
            )
            
            assert response.status_code == 422
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_schedule_invalid_days(self, test_client, mock_state):
        """Error cuando los días de la semana son inválidos."""
        invalid_data = {
            "vehicle_id": "TEST-001",
            "schedule": {
                "start_time": "06:00",
                "end_time": "22:00",
                "days_of_week": [0, 8, 9]  # Días inválidos
            }
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/schedule",
                json=invalid_data
            )
            
            assert response.status_code == 422
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_define_schedule_crossing_midnight(self, test_client, mock_state):
        """Definir horario que cruza la medianoche."""
        schedule_data = {
            "vehicle_id": "NIGHT-001",
            "schedule": {
                "start_time": "22:00",
                "end_time": "06:00",  # Cruza medianoche
                "days_of_week": [1, 2, 3]
            }
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/schedule",
                json=schedule_data
            )
            
            assert response.status_code == 201
            
            data = response.json()
            assert "22:00-06:00" in data["message"]


# ============================================================================
# TESTS PARA ENDPOINT /update-rule
# ============================================================================

class TestUpdateRuleEndpoint:
    """Tests para POST /update-rule."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_rule_success(self, test_client, mock_state):
        """Actualizar regla exitosamente."""
        update_data = {
            "vehicle_id": "TRUCK-001",
            "rule_type": "MAX_SPEED",
            "comparison_value": "90.0",
            "action_type": "NOTIFY_POLICE",
            "is_active": True
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/update-rule",
                json=update_data
            )
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "success"
            assert "Regla MAX_SPEED actualizada a 90.0" in data["message"]
            assert "rows_updated" in data
            
            # Verificar que se invalidó cache
            mock_state.redis.delete.assert_called()
            # Debería borrar ambas caches (normal y emergencia)
            assert mock_state.redis.delete.call_count >= 2
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_rule_with_redis_disabled(self, test_client, mock_state):
        """Actualizar regla cuando Redis está deshabilitado."""
        mock_state.redis_enabled = False
        
        update_data = {
            "vehicle_id": "TRUCK-001",
            "rule_type": "MAX_SPEED",
            "comparison_value": "80.0",
            "action_type": "NOTIFY_OWNER"
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/update-rule",
                json=update_data
            )
            
            assert response.status_code == 200
            # No debería intentar borrar cache
            mock_state.redis.delete.assert_not_called()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_rule_db_error(self, test_client, mock_state):
        """Manejar error al actualizar en base de datos."""
        update_data = {
            "vehicle_id": "TRUCK-001",
            "rule_type": "MAX_SPEED",
            "comparison_value": "90.0",
            "action_type": "NOTIFY_OWNER"
        }
        
        # Configurar error en DB
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_state.pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/update-rule",
                json=update_data
            )
            
            assert response.status_code == 500
            assert "Error actualizando regla" in response.json()["detail"]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_rule_invalid_enum_values(self, test_client, mock_state):
        """Error cuando los valores de enum son inválidos."""
        invalid_data = {
            "vehicle_id": "TRUCK-001",
            "rule_type": "INVALID_RULE_TYPE",  # No existe
            "comparison_value": "90.0",
            "action_type": "INVALID_ACTION"  # No existe
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/update-rule",
                json=invalid_data
            )
            
            assert response.status_code == 422  # Validation error
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_update_rule_cache_delete_error(self, test_client, mock_state):
        """Actualizar regla aún cuando falla borrar cache."""
        update_data = {
            "vehicle_id": "TRUCK-001",
            "rule_type": "MAX_SPEED",
            "comparison_value": "85.0",
            "action_type": "NOTIFY_OWNER"
        }
        
        # Configurar error al borrar cache
        mock_state.redis.delete = AsyncMock(side_effect=Exception("Cache delete error"))
        
        with patch('api.routes.state', mock_state):
            response = test_client.post(
                "/update-rule",
                json=update_data
            )
            
            # Aún debería ser exitoso (cache es optimización)
            assert response.status_code == 200
            assert "success" in response.json()["status"]


# ============================================================================
# TESTS PARA ENDPOINT /metrics
# ============================================================================

class TestMetricsEndpoint:
    """Tests para GET /metrics."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_metrics_success(self, test_client, mock_state):
        """Obtener métricas exitosamente."""
        # Configurar métricas de prueba
        mock_state.metrics = {
            "signals_processed": 1500,
            "alerts_generated": 45,
            "emergencies_processed": 3
        }
        
        # Configurar Redis info
        mock_state.redis.info = AsyncMock(return_value={
            "connected_clients": 5,
            "used_memory": 10485760  # 10MB
        })
        
        # Configurar DB para métricas
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=[62.5, 10, 9500, 120])
        mock_state.pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        with patch('api.routes.state', mock_state):
            response = test_client.get("/metrics")
            
            assert response.status_code == 200
            
            data = response.json()
            
            # Verificar estructura
            assert "system" in data
            assert "processing" in data
            assert "database" in data
            assert "redis" in data
            assert "queues" in data
            
            # Verificar valores
            assert data["processing"]["signals_processed"] == 1500
            assert data["database"]["signals_per_hour"] == 62.5
            assert data["redis"]["connected_clients"] == 5
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_metrics_with_redis_error(self, test_client, mock_state):
        """Obtener métricas cuando Redis falla."""
        mock_state.redis.info = AsyncMock(side_effect=Exception("Redis error"))
        
        with patch('api.routes.state', mock_state):
            response = test_client.get("/metrics")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["redis"]["error"] == "No disponible"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_metrics_with_db_error(self, test_client, mock_state):
        """Obtener métricas cuando DB falla."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("DB error"))
        mock_state.pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        with patch('api.routes.state', mock_state):
            response = test_client.get("/metrics")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["database"]["error"] == "No disponible"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_metrics_with_redis_disabled(self, test_client, mock_state):
        """Obtener métricas cuando Redis está deshabilitado."""
        mock_state.redis_enabled = False
        
        with patch('api.routes.state', mock_state):
            response = test_client.get("/metrics")
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["redis"]["enabled"] is False
            assert data["queues"]["normal_pending"] == 0  # Cuando redis disabled


# ============================================================================
# TESTS DE FLUJOS COMPLETOS
# ============================================================================

class TestCompleteWorkflows:
    """Tests que simulan flujos completos de usuario."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_complete_vehicle_monitoring_flow(self, test_client, mock_state):
        """Flujo completo: definir reglas, recibir señales, ver métricas."""
        
        with patch('api.routes.state', mock_state):
            # 1. Verificar salud del sistema
            health_response = test_client.get("/health")
            assert health_response.status_code == 200
            
            # 2. Definir geocerca para un vehículo
            geofence_data = {
                "vehicle_id": "TRUCK-001",
                "geofence": {
                    "name": "Zona_Norte",
                    "center": {"latitude": 4.60971, "longitude": -74.08175},
                    "radius_km": 5.0
                }
            }
            geofence_response = test_client.post("/geofence", json=geofence_data)
            assert geofence_response.status_code == 201
            
            # 3. Definir horario para otro vehículo
            schedule_data = {
                "vehicle_id": "MOTO-301",
                "schedule": {
                    "start_time": "06:00",
                    "end_time": "22:00",
                    "days_of_week": [1, 2, 3, 4, 5]
                }
            }
            schedule_response = test_client.post("/schedule", json=schedule_data)
            assert schedule_response.status_code == 201
            
            # 4. Actualizar regla de velocidad
            rule_update_data = {
                "vehicle_id": "TRUCK-001",
                "rule_type": "MAX_SPEED",
                "comparison_value": "85.0",
                "action_type": "NOTIFY_OWNER"
            }
            rule_response = test_client.post("/update-rule", json=rule_update_data)
            assert rule_response.status_code == 200
            
            # 5. Enviar señal normal
            signal_data = {
                "vehicle_id": "TRUCK-001",
                "speed": 80.5,  # Justo por encima del nuevo límite
                "latitude": 4.60971,
                "longitude": -74.08175,
                "timestamp": "2024-01-15T14:30:00Z"
            }
            signal_response = test_client.post("/signal", json=signal_data)
            assert signal_response.status_code == 202
            assert signal_response.json()["priority"] == "normal"
            
            # 6. Enviar señal de emergencia
            emergency_data = {
                "vehicle_id": "TAXI-101",
                "speed": 0.0,
                "latitude": 4.60971,
                "longitude": -74.08175,
                "panic_button": True
            }
            emergency_response = test_client.post("/signal", json=emergency_data)
            assert emergency_response.status_code == 202
            assert emergency_response.json()["priority"] == "emergency"
            
            # 7. Verificar métricas
            metrics_response = test_client.get("/metrics")
            assert metrics_response.status_code == 200
            metrics = metrics_response.json()
            
            # Las métricas deberían reflejar la actividad
            assert metrics["processing"]["signals_processed"] >= 0
            # (Nota: en realidad no se procesan porque los workers están mockeados)
            
            # 8. Verificar salud final
            final_health = test_client.get("/health")
            assert final_health.status_code == 200
            assert final_health.json()["status"] in ["healthy", "degraded"]
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, test_client, mock_state):
        """Flujo que prueba recuperación de errores."""
        
        with patch('api.routes.state', mock_state):
            # 1. Hacer fallar Redis temporalmente
            original_xadd = mock_state.redis.xadd
            mock_state.redis.xadd = AsyncMock(side_effect=Exception("Redis temporary failure"))
            
            # Intentar enviar señal (debería fallar)
            signal_data = {
                "vehicle_id": "TEST-001",
                "speed": 50.0,
                "latitude": 0.0,
                "longitude": 0.0
            }
            failed_response = test_client.post("/signal", json=signal_data)
            assert failed_response.status_code == 500
            
            # 2. Recuperar Redis
            mock_state.redis.xadd = original_xadd
            
            # Enviar señal nuevamente (debería funcionar)
            recovered_response = test_client.post("/signal", json=signal_data)
            assert recovered_response.status_code == 202
            
            # 3. Verificar que el sistema sigue funcionando
            health_response = test_client.get("/health")
            assert health_response.status_code == 200


# ============================================================================
# TESTS DE VALIDACIÓN Y SCHEMAS
# ============================================================================

class TestValidationAndSchemas:
    """Tests para validación de datos y schemas de respuesta."""
    
    @pytest.mark.integration
    def test_signal_response_schema(self, test_client, mock_state, sample_signal_data):
        """Verificar que la respuesta de /signal sigue el schema."""
        with patch('api.routes.state', mock_state):
            response = test_client.post("/signal", json=sample_signal_data)
            
            assert response.status_code == 202
            
            data = response.json()
            
            # Verificar schema mínimo
            required_fields = ["status", "vehicle_id", "message_id", 
                             "processing_time_ms", "timestamp", "priority"]
            
            for field in required_fields:
                assert field in data
            
            # Verificar tipos
            assert isinstance(data["status"], str)
            assert isinstance(data["vehicle_id"], str)
            assert isinstance(data["message_id"], str)
            assert isinstance(data["processing_time_ms"], (int, float))
            assert isinstance(data["timestamp"], str)
            assert isinstance(data["priority"], str)
            assert data["priority"] in ["normal", "emergency"]
    
    @pytest.mark.integration
    def test_health_response_schema(self, test_client, mock_state):
        """Verificar que la respuesta de /health sigue el schema."""
        with patch('api.routes.state', mock_state):
            response = test_client.get("/health")
            
            assert response.status_code == 200
            
            data = response.json()
            
            # Verificar schema
            assert "status" in data
            assert "services" in data
            assert "uptime_seconds" in data
            assert "timestamp" in data
            
            # Verificar estructura de services
            services = data["services"]
            assert "postgresql" in services
            assert "redis" in services
            assert "stream_normal" in services
            assert "stream_emergency" in services
            
            # Status válidos
            valid_statuses = ["healthy", "degraded", "unhealthy"]
            assert data["status"] in valid_statuses
            
            for service_status in services.values():
                assert service_status in ["healthy", "unhealthy", "circuit_open"]
    
    @pytest.mark.integration
    def test_metrics_response_structure(self, test_client, mock_state):
        """Verificar estructura de respuesta de /metrics."""
        with patch('api.routes.state', mock_state):
            response = test_client.get("/metrics")
            
            assert response.status_code == 200
            
            data = response.json()
            
            # Verificar secciones principales
            assert "system" in data
            assert "processing" in data
            assert "database" in data
            assert "redis" in data
            assert "queues" in data
            
            # Verificar system
            system = data["system"]
            assert "uptime_seconds" in system
            assert "api_instance" in system
            assert "timestamp" in system
            
            # Verificar processing (métricas básicas)
            processing = data["processing"]
            assert "signals_processed" in processing
            assert "alerts_generated" in processing
            assert "emergencies_processed" in processing


# ============================================================================
# TESTS DE RENDIMIENTO DE API
# ============================================================================

class TestAPIPerformance:
    """Tests que verifican rendimiento de endpoints."""
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_signal_endpoint_response_time(self, test_client, mock_state):
        """Verificar que /signal responde rápidamente."""
        import time
        
        signal_data = {
            "vehicle_id": "PERF-001",
            "speed": 50.0,
            "latitude": 0.0,
            "longitude": 0.0
        }
        
        with patch('api.routes.state', mock_state):
            # Medir tiempo de respuesta
            start = time.time()
            response = test_client.post("/signal", json=signal_data)
            end = time.time()
            
            response_time = (end - start) * 1000  # ms
            
            assert response.status_code == 202
            # Debería responder en menos de 100ms (en testing con mocks)
            assert response_time < 100
            
            # Verificar que el tiempo reportado es razonable
            reported_time = response.json()["processing_time_ms"]
            assert 0 <= reported_time <= response_time + 10  # Margen
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_health_endpoint_response_time(self, test_client, mock_state):
        """Verificar que /health responde rápidamente."""
        import time
        
        with patch('api.routes.state', mock_state):
            # Promedio de múltiples llamadas
            times = []
            for _ in range(5):
                start = time.time()
                response = test_client.get("/health")
                end = time.time()
                
                assert response.status_code == 200
                times.append((end - start) * 1000)
            
            avg_time = sum(times) / len(times)
            # /health debería ser muy rápido (< 50ms)
            assert avg_time < 50
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_client, mock_state):
        """Manejar múltiples solicitudes concurrentes."""
        import asyncio
        import concurrent.futures
        
        signal_data = {
            "vehicle_id": "CONCURRENT-001",
            "speed": 50.0,
            "latitude": 0.0,
            "longitude": 0.0
        }
        
        with patch('api.routes.state', mock_state):
            # Enviar 10 solicitudes "concurrentes"
            def send_request():
                return test_client.post("/signal", json=signal_data)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(send_request) for _ in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Todas deberían ser exitosas
            for response in results:
                assert response.status_code == 202


# ============================================================================
# TESTS DE ERROR HANDLING EN API
# ============================================================================

class TestAPIErrorHandling:
    """Tests para manejo de errores en la API."""
    
    @pytest.mark.integration
    def test_nonexistent_endpoint(self, test_client):
        """Endpoint inexistente debe retornar 404."""
        response = test_client.get("/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.integration
    def test_method_not_allowed(self, test_client):
        """Método HTTP no permitido debe retornar 405."""
        response = test_client.put("/health")
        assert response.status_code == 405
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_malformed_json(self, test_client):
        """JSON malformado debe retornar 422."""
        response = test_client.post(
            "/signal",
            content="{malformed json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_large_payload(self, test_client, mock_state):
        """Payload muy grande (potencial DoS)."""
        # Crear metadata muy grande
        large_metadata = {"data": "x" * 1000000}  # 1MB
        
        signal_data = {
            "vehicle_id": "TEST-001",
            "speed": 50.0,
            "latitude": 0.0,
            "longitude": 0.0,
            "metadata": large_metadata
        }
        
        with patch('api.routes.state', mock_state):
            response = test_client.post("/signal", json=signal_data)
            
            # Podría ser 202 (aceptado) o 413/422 (muy grande)
            # FastAPI por defecto no limita tamaño, pero validación Pydantic podría fallar
            assert response.status_code in [202, 413, 422, 500]


# ============================================================================
# TESTS DE HEADERS Y METADATA
# ============================================================================

class TestHeadersAndMetadata:
    """Tests para headers HTTP y metadata de respuestas."""
    
    @pytest.mark.integration
    def test_response_headers(self, test_client, mock_state):
        """Verificar headers en respuestas."""
        with patch('api.routes.state', mock_state):
            response = test_client.get("/health")
            
            # Headers importantes
            assert "content-type" in response.headers
            assert response.headers["content-type"] == "application/json"
            
            # CORS headers (si están configurados)
            # assert "access-control-allow-origin" in response.headers
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_request_content_type_validation(self, test_client, mock_state):
        """Validar Content-Type en requests."""
        signal_data = {
            "vehicle_id": "TEST-001",
            "speed": 50.0,
            "latitude": 0.0,
            "longitude": 0.0
        }
        
        with patch('api.routes.state', mock_state):
            # Sin Content-Type
            response = test_client.post(
                "/signal",
                json=signal_data,
                headers={"Content-Type": "text/plain"}  # Wrong content type
            )
            
            # FastAPI es flexible, generalmente acepta si el body es JSON válido
            # Pero verifiquemos que al menos procesa
            assert response.status_code in [202, 415, 422]