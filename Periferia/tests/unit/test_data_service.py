"""
tests/unit/test_data_service.py - Tests unitarios para DataService

Responsabilidades:
- Testear operaciones de base de datos (CRUD)
- Verificar caching con Redis
- Usar mocks para asyncpg y redis

Características:
- @pytest.mark.unit: Tests rápidos, sin dependencias reales
- Mocks completos de PostgreSQL y Redis
- Tests aislados de infraestructura
"""

import json
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch
import pytest

from domain.models import Signal, VehicleType
from application.services import DataService


# ============================================================================
# FIXTURES PARA TESTS DE DATA SERVICE
# ============================================================================

@pytest.fixture
def mock_pool():
    """Mock completo de asyncpg.Pool."""
    pool = AsyncMock()
    
    # Configurar conexión mock
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=None)
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    conn.executemany = AsyncMock(return_value=None)
    
    # Configurar context manager
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=None)
    
    pool.acquire = AsyncMock(return_value=conn.__aenter__())
    
    return pool

@pytest.fixture
def mock_redis():
    """Mock completo de Redis client."""
    redis = AsyncMock()
    
    # Configurar métodos comunes
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.ping = AsyncMock(return_value=True)
    
    return redis

@pytest.fixture
def sample_signal():
    """Señal de prueba para operaciones de persistencia."""
    return Signal(
        vehicle_id="TRUCK-001",
        speed=75.5,
        latitude=4.60971,
        longitude=-74.08175,
        timestamp=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        panic_button=False,
        temperature=-15.0,
        vehicle_type=VehicleType.TRUCK,
        metadata={
            "cargo_type": "pharmaceuticals",
            "door_status": "closed"
        }
    )

@pytest.fixture
def sample_emergency_signal():
    """Señal de emergencia para pruebas específicas."""
    return Signal(
        vehicle_id="TAXI-101",
        speed=0.0,
        latitude=4.60971,
        longitude=-74.08175,
        timestamp=datetime.utcnow(),
        panic_button=True,
        temperature=None,
        vehicle_type=VehicleType.CAR,
        metadata={}
    )

@pytest.fixture
def sample_rules_data():
    """Datos de reglas para pruebas de cache."""
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
        }
    ]


# ============================================================================
# TESTS PARA PERSISTENCIA DE SEÑALES
# ============================================================================

class TestPersistSignal:
    """Tests para persist_signal()."""
    
    @pytest.mark.asyncio
    async def test_persist_signal_success(self, sample_signal, mock_pool):
        """Persistir señal exitosamente."""
        # Configurar mock para retornar un ID
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=12345)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        signal_id = await DataService.persist_signal(
            signal=sample_signal,
            pool=mock_pool,
            api_instance_id="test-api-001"
        )
        
        assert signal_id == 12345
        
        # Verificar que se llamó a execute con los parámetros correctos
        mock_conn.fetchval.assert_called_once()
        call_args = mock_conn.fetchval.call_args
        
        # Verificar parámetros básicos
        assert call_args[0][0] == "TRUCK-001"  # vehicle_id
        assert call_args[0][1] == sample_signal.timestamp  # timestamp
        assert call_args[0][2] == 4.60971  # latitude
        assert call_args[0][3] == -74.08175  # longitude
        assert call_args[0][4] == 75.5  # speed
        assert call_args[0][5] == 0.0  # heading
        
        # Verificar metadata
        metadata = json.loads(call_args[0][6])
        assert metadata["panic_button"] is False
        assert metadata["temperature"] == -15.0
        assert metadata["vehicle_type"] == "TRUCK"
        assert metadata["cargo_type"] == "pharmaceuticals"
        assert "processed_at" in metadata
        assert metadata["api_instance"] == "test-api-001"
    
    @pytest.mark.asyncio
    async def test_persist_signal_with_minimal_data(self, mock_pool):
        """Persistir señal con datos mínimos."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0
            # Sin metadata, sin tipo, sin temperatura
        )
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=999)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        signal_id = await DataService.persist_signal(
            signal=signal,
            pool=mock_pool,
            api_instance_id="minimal-test"
        )
        
        assert signal_id == 999
        
        # Verificar metadata generada
        call_args = mock_conn.fetchval.call_args
        metadata = json.loads(call_args[0][6])
        
        assert metadata["panic_button"] is False
        assert metadata["temperature"] is None
        assert metadata["vehicle_type"] is None
        assert metadata == {
            "panic_button": False,
            "temperature": None,
            "vehicle_type": None,
            "processed_at": metadata["processed_at"],  # Verificar que existe
            "api_instance": "minimal-test"
        }
    
    @pytest.mark.asyncio
    async def test_persist_signal_with_panic_button(self, mock_pool):
        """Persistir señal con botón de pánico activado."""
        signal = Signal(
            vehicle_id="EMERGENCY-001",
            speed=0.0,
            latitude=0.0,
            longitude=0.0,
            panic_button=True,
            metadata={"emergency_type": "assault"}
        )
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=777)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        signal_id = await DataService.persist_signal(
            signal=signal,
            pool=mock_pool,
            api_instance_id="emergency-api"
        )
        
        # Verificar metadata incluye panic_button
        call_args = mock_conn.fetchval.call_args
        metadata = json.loads(call_args[0][6])
        
        assert metadata["panic_button"] is True
        assert metadata["emergency_type"] == "assault"
    
    @pytest.mark.asyncio
    async def test_persist_signal_db_error_handling(self, sample_signal, mock_pool):
        """Manejar error de base de datos al persistir."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("DB connection failed"))
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        # Debería propagar la excepción
        with pytest.raises(Exception) as exc_info:
            await DataService.persist_signal(
                signal=sample_signal,
                pool=mock_pool,
                api_instance_id="test"
            )
        
        assert "DB connection failed" in str(exc_info.value)


class TestPersistEmergencySignal:
    """Tests para persist_emergency_signal() (más rápido)."""
    
    @pytest.mark.asyncio
    async def test_persist_emergency_signal_success(self, sample_emergency_signal, mock_pool):
        """Persistir señal de emergencia exitosamente."""
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=888)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        signal_id = await DataService.persist_emergency_signal(
            signal=sample_emergency_signal,
            pool=mock_pool
        )
        
        assert signal_id == 888
        
        # Verificar que se usan menos campos (más rápido)
        call_args = mock_conn.fetchval.call_args
        
        # Solo campos esenciales
        assert call_args[0][0] == "TAXI-101"  # vehicle_id
        assert call_args[0][4] == 0.0  # speed
        
        # Metadata mínima para emergencia
        metadata = json.loads(call_args[0][6])
        assert metadata == {
            "emergency": True,
            "panic_button": True
        }
    
    @pytest.mark.asyncio
    async def test_persist_emergency_signal_without_panic(self, mock_pool):
        """Persistir como emergencia incluso sin panic_button (por si acaso)."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=100.0,  # Alta velocidad podría ser emergencia
            latitude=0.0,
            longitude=0.0,
            panic_button=False  # No botón pánico, pero aún es "emergency"
        )
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=111)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        signal_id = await DataService.persist_emergency_signal(
            signal=signal,
            pool=mock_pool
        )
        
        # Verificar metadata
        call_args = mock_conn.fetchval.call_args
        metadata = json.loads(call_args[0][6])
        
        assert metadata["emergency"] is True
        assert metadata["panic_button"] is False  # Refleja el valor real


# ============================================================================
# TESTS PARA OBTENCIÓN DE REGLAS (CON CACHE)
# ============================================================================

class TestGetRules:
    """Tests para get_rules() con cache en Redis."""
    
    @pytest.mark.asyncio
    async def test_get_rules_from_cache_hit(self, mock_pool, mock_redis):
        """Obtener reglas desde cache (hit)."""
        vehicle_id = "TRUCK-001"
        cache_key = f"rules:{vehicle_id}"
        cached_rules = [
            {"id": 1, "rule_type": "MAX_SPEED", "comparison_value": "80.0"}
        ]
        
        # Configurar Redis para retornar cache
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_rules))
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        # Debería usar cache, no llamar a DB
        assert rules == cached_rules
        mock_redis.get.assert_called_once_with(cache_key)
        mock_pool.acquire.assert_not_called()  # No debería tocar la DB
    
    @pytest.mark.asyncio
    async def test_get_rules_from_database_cache_miss(self, mock_pool, mock_redis):
        """Obtener reglas desde DB cuando no hay cache (miss)."""
        vehicle_id = "TRUCK-001"
        cache_key = f"rules:{vehicle_id}"
        db_rules = [
            {"id": 1, "rule_type": "MAX_SPEED", "comparison_value": "80.0", "action_type": "NOTIFY_OWNER", "priority": 1},
            {"id": 2, "rule_type": "PANIC_BUTTON", "comparison_value": "TRUE", "action_type": "NOTIFY_POLICE", "priority": 10}
        ]
        
        # Configurar cache miss
        mock_redis.get = AsyncMock(return_value=None)
        
        # Configurar DB para retornar reglas
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"id": 1, "rule_type": "MAX_SPEED", "comparison_value": "80.0", "action_type": "NOTIFY_OWNER", "priority": 1},
            {"id": 2, "rule_type": "PANIC_BUTTON", "comparison_value": "TRUE", "action_type": "NOTIFY_POLICE", "priority": 10}
        ])
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        # Debería obtener de DB y guardar en cache
        assert len(rules) == 2
        assert rules[0]["rule_type"] == "MAX_SPEED"
        
        # Verificar llamadas
        mock_redis.get.assert_called_once_with(cache_key)
        mock_conn.fetch.assert_called_once()
        mock_redis.setex.assert_called_once_with(
            cache_key, 
            300,  # TTL de 5 minutos
            json.dumps(db_rules, default=str)
        )
    
    @pytest.mark.asyncio
    async def test_get_rules_with_redis_disabled(self, mock_pool, mock_redis):
        """Obtener reglas cuando Redis está deshabilitado."""
        vehicle_id = "TRUCK-001"
        db_rules = [{"id": 1, "rule_type": "MAX_SPEED", "comparison_value": "80.0"}]
        
        # Configurar DB
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=db_rules)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=False  # Redis deshabilitado
        )
        
        # Debería ir directo a DB, sin tocar Redis
        assert rules == db_rules
        mock_redis.get.assert_not_called()
        mock_redis.setex.assert_not_called()
        mock_conn.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_rules_empty_result(self, mock_pool, mock_redis):
        """Obtener reglas cuando no hay reglas para el vehículo."""
        vehicle_id = "NO-RULES-001"
        
        # Cache miss
        mock_redis.get = AsyncMock(return_value=None)
        
        # DB retorna vacío
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        assert rules == []
        
        # No debería guardar cache vacío
        mock_redis.setex.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_rules_cache_timeout(self, mock_pool, mock_redis):
        """Manejar timeout al obtener cache."""
        vehicle_id = "TRUCK-001"
        
        # Simular timeout en Redis
        mock_redis.get = AsyncMock(side_effect=asyncio.TimeoutError("Redis timeout"))
        
        # Configurar DB como fallback
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"id": 1, "rule_type": "MAX_SPEED"}])
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        # Debería fallar a DB
        assert len(rules) == 1
        mock_redis.get.assert_called_once()
        mock_conn.fetch.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_rules_db_timeout(self, mock_pool, mock_redis):
        """Manejar timeout en consulta a DB."""
        vehicle_id = "TRUCK-001"
        
        # Cache miss
        mock_redis.get = AsyncMock(return_value=None)
        
        # DB timeout
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=asyncio.TimeoutError("DB timeout"))
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        # Debería retornar lista vacía en caso de timeout
        assert rules == []
    
    @pytest.mark.asyncio
    async def test_get_rules_cache_set_timeout(self, mock_pool, mock_redis):
        """Manejar timeout al guardar en cache."""
        vehicle_id = "TRUCK-001"
        db_rules = [{"id": 1, "rule_type": "MAX_SPEED"}]
        
        # Cache miss
        mock_redis.get = AsyncMock(return_value=None)
        
        # DB retorna reglas
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=db_rules)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        # Timeout al guardar cache
        mock_redis.setex = AsyncMock(side_effect=asyncio.TimeoutError("Cache set timeout"))
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        # Debería retornar reglas aunque falle cache
        assert rules == db_rules
        mock_redis.setex.assert_called_once()


class TestGetEmergencyRules:
    """Tests para get_emergency_rules() (solo PANIC_BUTTON)."""
    
    @pytest.mark.asyncio
    async def test_get_emergency_rules_cache_hit(self, mock_pool, mock_redis):
        """Obtener reglas de emergencia desde cache."""
        vehicle_id = "TAXI-101"
        cache_key = f"emergency_rules:{vehicle_id}"
        cached_rules = [
            {"id": 2, "rule_type": "PANIC_BUTTON", "comparison_value": "TRUE", "action_type": "NOTIFY_POLICE"}
        ]
        
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_rules))
        
        rules = await DataService.get_emergency_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        assert rules == cached_rules
        mock_redis.get.assert_called_once_with(cache_key)
        mock_pool.acquire.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_emergency_rules_db_query(self, mock_pool, mock_redis):
        """Obtener reglas de emergencia desde DB."""
        vehicle_id = "TAXI-101"
        
        # Cache miss
        mock_redis.get = AsyncMock(return_value=None)
        
        # DB retorna regla de pánico
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"id": 2, "rule_type": "PANIC_BUTTON", "comparison_value": "TRUE", "action_type": "NOTIFY_POLICE"}
        ])
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_emergency_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        assert len(rules) == 1
        assert rules[0]["rule_type"] == "PANIC_BUTTON"
        
        # Verificar query específica
        mock_conn.fetch.assert_called_once()
        query = mock_conn.fetch.call_args[0][0]
        assert "rule_type = 'PANIC_BUTTON'" in query
        
        # Verificar cache con TLL más largo (10 minutos)
        mock_redis.setex.assert_called_once_with(
            f"emergency_rules:{vehicle_id}",
            600,  # 10 minutos para emergencias
            json.dumps(rules, default=str)
        )
    
    @pytest.mark.asyncio
    async def test_get_emergency_rules_no_panic_rules(self, mock_pool, mock_redis):
        """Cuando no hay reglas de pánico para el vehículo."""
        vehicle_id = "NO-PANIC-001"
        
        mock_redis.get = AsyncMock(return_value=None)
        
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])  # Sin reglas de pánico
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_emergency_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        assert rules == []
        # No debería guardar cache vacío
        mock_redis.setex.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_emergency_rules_with_other_rules_in_db(self, mock_pool, mock_redis):
        """DB tiene reglas pero no de PANIC_BUTTON."""
        vehicle_id = "TRUCK-001"
        
        mock_redis.get = AsyncMock(return_value=None)
        
        # DB retorna otras reglas, pero no PANIC_BUTTON
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"id": 1, "rule_type": "MAX_SPEED", "comparison_value": "80.0", "action_type": "NOTIFY_OWNER"}
            # Sin PANIC_BUTTON
        ])
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_emergency_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        # Solo debería retornar PANIC_BUTTON, que no hay
        assert rules == []


# ============================================================================
# TESTS PARA BULK INSERT DE ALERTAS
# ============================================================================

class TestBulkInsertAlerts:
    """Tests para bulk_insert_alerts()."""
    
    @pytest.mark.asyncio
    async def test_bulk_insert_alerts_success(self, mock_pool):
        """Insertar múltiples alertas exitosamente."""
        alerts_to_insert = [
            ("TRUCK-001", 1, 123, "Exceso velocidad", "NOTIFY_OWNER", datetime.utcnow()),
            ("TRUCK-001", 2, 123, "Botón pánico", "NOTIFY_POLICE", datetime.utcnow()),
            ("TAXI-101", 1, 456, "Exceso velocidad", "SMS_OWNER", datetime.utcnow())
        ]
        
        mock_conn = AsyncMock()
        mock_conn.executemany = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        await DataService.bulk_insert_alerts(
            alerts_to_insert=alerts_to_insert,
            pool=mock_pool
        )
        
        # Verificar que se llamó a executemany con los datos correctos
        mock_conn.executemany.assert_called_once()
        
        # Verificar query
        query = mock_conn.executemany.call_args[0][0]
        assert "INSERT INTO alerts" in query
        
        # Verificar datos
        data = mock_conn.executemany.call_args[0][1]
        assert len(data) == 3
        assert data[0][0] == "TRUCK-001"
        assert data[0][3] == "Exceso velocidad"
    
    @pytest.mark.asyncio
    async def test_bulk_insert_alerts_empty_list(self, mock_pool):
        """No hacer nada cuando la lista está vacía."""
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        await DataService.bulk_insert_alerts(
            alerts_to_insert=[],
            pool=mock_pool
        )
        
        # No debería llamar a executemany
        mock_conn.executemany.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_bulk_insert_alerts_single_alert(self, mock_pool):
        """Insertar una sola alerta."""
        single_alert = [
            ("TRUCK-001", 1, 123, "Test alert", "LOG_ONLY", datetime.utcnow())
        ]
        
        mock_conn = AsyncMock()
        mock_conn.executemany = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        await DataService.bulk_insert_alerts(
            alerts_to_insert=single_alert,
            pool=mock_pool
        )
        
        mock_conn.executemany.assert_called_once()
        data = mock_conn.executemany.call_args[0][1]
        assert len(data) == 1
    
    @pytest.mark.asyncio
    async def test_bulk_insert_alerts_db_error(self, mock_pool):
        """Manejar error en inserción masiva."""
        alerts = [
            ("TRUCK-001", 1, 123, "Test", "NOTIFY_OWNER", datetime.utcnow())
        ]
        
        mock_conn = AsyncMock()
        mock_conn.executemany = AsyncMock(side_effect=Exception("DB error"))
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        # Debería propagar la excepción
        with pytest.raises(Exception) as exc_info:
            await DataService.bulk_insert_alerts(
                alerts_to_insert=alerts,
                pool=mock_pool
            )
        
        assert "DB error" in str(exc_info.value)


# ============================================================================
# TESTS PARA CONVERSIONES Y UTILIDADES
# ============================================================================

class TestDataConversions:
    """Tests para conversiones de datos en DataService."""
    
    def test_json_serialization_of_datetime(self):
        """Verificar que datetime se serializa correctamente."""
        from datetime import datetime
        
        # Datos con datetime
        data = {
            "timestamp": datetime(2024, 1, 15, 10, 30, 0),
            "number": 123,
            "string": "test"
        }
        
        # json.dumps con default=str debería manejar datetime
        json_str = json.dumps(data, default=str)
        parsed = json.loads(json_str)
        
        assert parsed["timestamp"] == "2024-01-15 10:30:00"
        assert parsed["number"] == 123
    
    @pytest.mark.asyncio
    async def test_persist_signal_json_serialization_edge_cases(self, mock_pool):
        """Manejar edge cases en serialización JSON."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0,
            metadata={
                "nested": {
                    "deep": {
                        "value": 123,
                        "list": [1, 2, 3],
                        "none": None
                    }
                },
                "special_chars": "áéíóú ñ",
                "boolean": True,
                "float": 3.14159
            }
        )
        
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=999)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        await DataService.persist_signal(
            signal=signal,
            pool=mock_pool,
            api_instance_id="test"
        )
        
        # Verificar que la serialización funciona con datos complejos
        call_args = mock_conn.fetchval.call_args
        metadata = json.loads(call_args[0][6])
        
        assert metadata["nested"]["deep"]["value"] == 123
        assert metadata["nested"]["deep"]["list"] == [1, 2, 3]
        assert metadata["nested"]["deep"]["none"] is None
        assert metadata["special_chars"] == "áéíóú ñ"
        assert metadata["boolean"] is True
        assert metadata["float"] == 3.14159


# ============================================================================
# TESTS DE INTEGRACIÓN ENTRE MÉTODOS
# ============================================================================

class TestIntegrationScenarios:
    """Tests que simulan flujos completos."""
    
    @pytest.mark.asyncio
    async def test_complete_flow_with_cache(self, sample_signal, mock_pool, mock_redis):
        """Flujo completo: obtener reglas, persistir señal, insertar alertas."""
        vehicle_id = "TRUCK-001"
        
        # 1. Configurar cache miss para reglas
        mock_redis.get = AsyncMock(return_value=None)
        
        # 2. Configurar DB para retornar reglas
        db_rules = [
            {"id": 1, "rule_type": "MAX_SPEED", "comparison_value": "80.0", "action_type": "NOTIFY_OWNER", "priority": 1}
        ]
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=db_rules)
        mock_conn.fetchval = AsyncMock(return_value=123)  # Para persist_signal
        mock_conn.executemany = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        # 3. Obtener reglas (debería ir a DB y guardar cache)
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        assert len(rules) == 1
        
        # 4. Persistir señal
        signal_id = await DataService.persist_signal(
            signal=sample_signal,
            pool=mock_pool,
            api_instance_id="test-flow"
        )
        
        assert signal_id == 123
        
        # 5. Simular que RuleService generó alertas
        alerts = [
            (vehicle_id, 1, signal_id, "Exceso velocidad: 75.5 > 80.0 km/h", "NOTIFY_OWNER", datetime.utcnow())
        ]
        
        # 6. Insertar alertas
        await DataService.bulk_insert_alerts(
            alerts_to_insert=alerts,
            pool=mock_pool
        )
        
        # Verificar todas las interacciones
        mock_redis.get.assert_called_once_with(f"rules:{vehicle_id}")
        mock_redis.setex.assert_called_once_with(f"rules:{vehicle_id}", 300, json.dumps(db_rules, default=str))
        assert mock_conn.fetch.call_count == 1  # Para get_rules
        assert mock_conn.fetchval.call_count == 1  # Para persist_signal
        assert mock_conn.executemany.call_count == 1  # Para bulk_insert_alerts
    
    @pytest.mark.asyncio
    async def test_emergency_flow_fast_path(self, sample_emergency_signal, mock_pool, mock_redis):
        """Flujo de emergencia usando métodos optimizados."""
        vehicle_id = "TAXI-101"
        
        # 1. Cache hit para reglas de emergencia
        emergency_rules = [
            {"id": 2, "rule_type": "PANIC_BUTTON", "comparison_value": "TRUE", "action_type": "NOTIFY_POLICE"}
        ]
        mock_redis.get = AsyncMock(return_value=json.dumps(emergency_rules))
        
        # 2. Configurar métodos rápidos
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(return_value=456)  # Para persist_emergency_signal
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        # 3. Obtener solo reglas de emergencia (desde cache)
        rules = await DataService.get_emergency_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        assert rules == emergency_rules
        
        # 4. Persistir con método rápido de emergencia
        signal_id = await DataService.persist_emergency_signal(
            signal=sample_emergency_signal,
            pool=mock_pool
        )
        
        assert signal_id == 456
        
        # Verificar que fue rápido (solo cache y persistencia simple)
        mock_redis.get.assert_called_once_with(f"emergency_rules:{vehicle_id}")
        mock_pool.acquire.assert_called_once()  # Solo para persistir
        # No debería llamar a get_rules (más lento) ni a setex (cache ya existe)


# ============================================================================
# TESTS DE PERFORMANCE/RENDIMIENTO
# ============================================================================

class TestPerformance:
    """Tests que verifican comportamiento de rendimiento."""
    
    @pytest.mark.asyncio
    async def test_get_rules_timeout_configuration(self, mock_pool, mock_redis):
        """Verificar que los timeouts se respetan."""
        vehicle_id = "TEST-001"
        
        # Configurar timeout en Redis
        mock_redis.get = AsyncMock(side_effect=asyncio.TimeoutError)
        
        # El método debería manejar el timeout rápidamente
        import time
        start = time.time()
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        elapsed = time.time() - start
        
        # Debería ser rápido (timeout de 0.5s en get)
        assert elapsed < 1.0
        assert rules == []  # Timeout resulta en lista vacía
    
    @pytest.mark.asyncio
    async def test_bulk_insert_performance_large_batch(self, mock_pool):
        """Verificar que bulk_insert maneja grandes lotes eficientemente."""
        # Crear 1000 alertas de prueba
        alerts = []
        for i in range(1000):
            alerts.append(
                (f"VEHICLE-{i % 100}", i % 10, 1000 + i, f"Alert {i}", "LOG_ONLY", datetime.utcnow())
            )
        
        mock_conn = AsyncMock()
        mock_conn.executemany = AsyncMock(return_value=None)
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        # Esto debería ser una sola operación en DB
        await DataService.bulk_insert_alerts(
            alerts_to_insert=alerts,
            pool=mock_pool
        )
        
        # Solo una llamada a executemany
        mock_conn.executemany.assert_called_once()
        
        # Todos los datos en un solo batch
        data = mock_conn.executemany.call_args[0][1]
        assert len(data) == 1000


# ============================================================================
# TESTS PARA ERRORES Y CASOS EXCEPCIONALES
# ============================================================================

class TestErrorCases:
    """Tests para casos de error y excepciones."""
    
    @pytest.mark.asyncio
    async def test_get_rules_with_null_redis(self, mock_pool):
        """Manejar cuando redis es None."""
        rules = await DataService.get_rules(
            vehicle_id="TEST-001",
            pool=mock_pool,
            redis=None,  # Redis es None
            redis_enabled=True
        )
        
        # Debería fallar a DB
        assert rules == []
    
    @pytest.mark.asyncio
    async def test_persist_signal_with_json_serialization_error(self, mock_pool):
        """Manejar error en serialización JSON."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0
        )
        
        # Hacer que json.dumps falle
        with patch('json.dumps', side_effect=Exception("JSON error")):
            with pytest.raises(Exception) as exc_info:
                await DataService.persist_signal(
                    signal=signal,
                    pool=mock_pool,
                    api_instance_id="test"
                )
            
            assert "JSON error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_rules_with_corrupted_cache(self, mock_pool, mock_redis):
        """Manejar cache corrupto (JSON inválido)."""
        vehicle_id = "TEST-001"
        
        # Redis retorna JSON inválido
        mock_redis.get = AsyncMock(return_value="{invalid json")
        
        # Debería fallar a DB
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"id": 1, "rule_type": "MAX_SPEED"}])
        mock_pool.acquire.return_value = mock_conn.__aenter__()
        
        rules = await DataService.get_rules(
            vehicle_id=vehicle_id,
            pool=mock_pool,
            redis=mock_redis,
            redis_enabled=True
        )
        
        # Debería obtener de DB
        assert len(rules) == 1
        mock_conn.fetch.assert_called_once()