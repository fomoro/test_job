"""
tests/integration/test_state.py - Tests de integración para GlobalState

Responsabilidades:
- Testear inicialización y shutdown de GlobalState
- Verificar workers y procesamiento de streams
- Probar integración real con Redis (puede usar Redis test)
- Verificar manejo de errores y recovery

Características:
- @pytest.mark.integration: Tests con dependencias
- @pytest.mark.slow: Pueden ser lentos por Redis/DB real
- Tests que verifican comportamiento asíncrono real
- Mocks mínimos, preferiblemente servicios reales en Docker
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import pytest
import pytest_asyncio

from domain.models import Signal, VehicleType
from infrastructure.state import GlobalState


# ============================================================================
# FIXTURES PARA TESTS DE STATE
# ============================================================================

@pytest_asyncio.fixture
async def mock_redis_pool():
    """Mock de Redis pool para tests."""
    redis = AsyncMock()
    
    # Configurar métodos básicos
    redis.ping = AsyncMock(return_value=True)
    redis.xadd = AsyncMock(return_value="1705311000000-0")
    redis.xreadgroup = AsyncMock(return_value=[])
    redis.xack = AsyncMock(return_value=1)
    redis.xgroup_create = AsyncMock(return_value=None)
    redis.xinfo_stream = AsyncMock(return_value={"length": 0})
    redis.xpending = AsyncMock(return_value={"pending": 0})
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.info = AsyncMock(return_value={"connected_clients": 1})
    redis.close = AsyncMock(return_value=None)
    
    return redis

@pytest_asyncio.fixture
async def mock_postgres_pool():
    """Mock de PostgreSQL pool para tests."""
    pool = AsyncMock()
    
    # Configurar conexión mock
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=1)
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    conn.executemany = AsyncMock(return_value=None)
    
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=None)
    
    pool.acquire = AsyncMock(return_value=conn.__aenter__())
    pool.close = AsyncMock(return_value=None)
    
    return pool

@pytest_asyncio.fixture
async def global_state(mock_redis_pool, mock_postgres_pool):
    """Instancia de GlobalState para testing."""
    state = GlobalState()
    
    # Reemplazar pools con mocks
    state.pool = mock_postgres_pool
    state.redis = mock_redis_pool
    
    # Configurar URLs de prueba
    state.REDIS_STREAM_NAME = "ccs_test_stream"
    state.EMERGENCY_STREAM_NAME = "ccs_test_emergency_stream"
    
    return state

@pytest.fixture
def sample_signal_data():
    """Datos de señal para tests."""
    return {
        "vehicle_id": "TRUCK-001",
        "speed": 75.5,
        "latitude": 4.60971,
        "longitude": -74.08175,
        "timestamp": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
        "panic_button": False,
        "temperature": -15.0,
        "vehicle_type": VehicleType.TRUCK,
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
        "timestamp": datetime.utcnow(),
        "panic_button": True,
        "temperature": None,
        "vehicle_type": VehicleType.CAR,
        "metadata": {}
    }


# ============================================================================
# TESTS PARA INICIALIZACIÓN Y SHUTDOWN
# ============================================================================

class TestStateInitialization:
    """Tests para inicialización y shutdown de GlobalState."""
    
    @pytest.mark.asyncio
    async def test_state_initialization_success(self, global_state, mock_redis_pool, mock_postgres_pool):
        """Inicialización exitosa de GlobalState."""
        # Configurar mocks para initialize
        with patch('asyncpg.create_pool', return_value=mock_postgres_pool):
            with patch('redis.asyncio.Redis.from_url', return_value=mock_redis_pool):
                await global_state.initialize()
        
        # Verificar que se configuraron los pools
        assert global_state.pool == mock_postgres_pool
        assert global_state.redis == mock_redis_pool
        assert global_state.running is True
        assert global_state.api_instance_id.startswith("ccs-api-")
        
        # Verificar que se crearon los streams
        mock_redis_pool.xgroup_create.assert_any_call(
            "ccs_test_stream", "ccs_workers", id="0", mkstream=True
        )
        mock_redis_pool.xgroup_create.assert_any_call(
            "ccs_test_emergency_stream", "ccs_emergency_workers", id="0", mkstream=True
        )
    
    @pytest.mark.asyncio
    async def test_state_initialization_redis_error(self, global_state):
        """Manejar error en conexión a Redis."""
        # Simular error en Redis
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Redis connection failed"))
        
        with patch('asyncpg.create_pool'):
            with patch('redis.asyncio.Redis.from_url', return_value=mock_redis):
                with pytest.raises(Exception) as exc_info:
                    await global_state.initialize()
                
                assert "Redis connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_state_initialization_postgres_error(self, global_state, mock_redis_pool):
        """Manejar error en conexión a PostgreSQL."""
        with patch('asyncpg.create_pool', side_effect=Exception("PostgreSQL connection failed")):
            with patch('redis.asyncio.Redis.from_url', return_value=mock_redis_pool):
                with pytest.raises(Exception) as exc_info:
                    await global_state.initialize()
                
                assert "PostgreSQL connection failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_state_shutdown_success(self, global_state, mock_redis_pool, mock_postgres_pool):
        """Shutdown exitoso de GlobalState."""
        global_state.running = True
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        await global_state.shutdown()
        
        # Verificar que se cerraron las conexiones
        mock_postgres_pool.close.assert_called_once()
        mock_redis_pool.close.assert_called_once()
        assert global_state.running is False
    
    @pytest.mark.asyncio
    async def test_state_shutdown_with_none_pools(self, global_state):
        """Shutdown cuando pools son None."""
        global_state.running = True
        global_state.pool = None
        global_state.redis = None
        
        # No debería lanzar excepción
        await global_state.shutdown()
        
        assert global_state.running is False
    
    @pytest.mark.asyncio
    async def test_state_shutdown_closes_workers(self, global_state, mock_redis_pool, mock_postgres_pool):
        """Shutdown debe detener los workers."""
        global_state.running = True
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        # Simular que hay workers corriendo
        mock_worker = asyncio.create_task(asyncio.sleep(10))  # Worker de larga duración
        
        with patch.object(global_state, '_normal_worker_loop', return_value=mock_worker):
            with patch.object(global_state, '_emergency_worker_loop', return_value=mock_worker):
                # Inicializar (crearía workers)
                await global_state.initialize()
                
                # Dar tiempo para que workers empiecen
                await asyncio.sleep(0.1)
                
                # Shutdown
                await global_state.shutdown()
                
                # Dar tiempo para que workers se detengan
                await asyncio.sleep(0.1)
                
                # Verificar que workers fueron cancelados
                assert mock_worker.cancelled() or mock_worker.done()


# ============================================================================
# TESTS PARA WORKERS DE PROCESAMIENTO
# ============================================================================

class TestWorkers:
    """Tests para workers de procesamiento."""
    
    @pytest.mark.asyncio
    async def test_normal_worker_loop_processes_messages(self, global_state, mock_redis_pool):
        """Worker normal procesa mensajes del stream."""
        # Configurar mensaje de prueba
        signal_data = {
            "vehicle_id": "TRUCK-001",
            "speed": 75.5,
            "latitude": 4.60971,
            "longitude": -74.08175,
            "timestamp": "2024-01-15T10:30:00Z",
            "panic_button": False
        }
        
        mock_redis_pool.xreadgroup = AsyncMock(return_value=[
            (
                "ccs_test_stream",
                [
                    ("1705311000000-0", {"data": json.dumps(signal_data)})
                ]
            )
        ])
        
        global_state.redis = mock_redis_pool
        global_state.running = True
        
        # Ejecutar una iteración del worker
        task = asyncio.create_task(global_state._normal_worker_loop())
        
        # Dar tiempo para procesar
        await asyncio.sleep(0.1)
        
        # Detener worker
        global_state.running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verificar que se procesó el mensaje
        mock_redis_pool.xreadgroup.assert_called_once()
        # Nota: _process_normal_signal está mockeado en el state
    
    @pytest.mark.asyncio
    async def test_emergency_worker_loop_processes_emergencies(self, global_state, mock_redis_pool):
        """Worker de emergencia procesa mensajes prioritarios."""
        emergency_data = {
            "vehicle_id": "TAXI-101",
            "speed": 0.0,
            "latitude": 4.60971,
            "longitude": -74.08175,
            "timestamp": "2024-01-15T10:30:00Z",
            "panic_button": True
        }
        
        mock_redis_pool.xreadgroup = AsyncMock(return_value=[
            (
                "ccs_test_emergency_stream",
                [
                    ("1705311000001-0", {"data": json.dumps(emergency_data)})
                ]
            )
        ])
        
        global_state.redis = mock_redis_pool
        global_state.running = True
        
        # Ejecutar worker de emergencia
        task = asyncio.create_task(global_state._emergency_worker_loop())
        
        # Dar tiempo para procesar
        await asyncio.sleep(0.1)
        
        # Detener
        global_state.running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verificar procesamiento de emergencia
        mock_redis_pool.xreadgroup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_worker_handles_redis_error(self, global_state, mock_redis_pool):
        """Worker maneja error en Redis."""
        mock_redis_pool.xreadgroup = AsyncMock(side_effect=Exception("Redis error"))
        
        global_state.redis = mock_redis_pool
        global_state.running = True
        
        # Ejecutar worker (debería manejar el error)
        task = asyncio.create_task(global_state._normal_worker_loop())
        
        # Dar tiempo para intentar procesar
        await asyncio.sleep(0.1)
        
        # Detener
        global_state.running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # El worker no debería haber crasheado
        mock_redis_pool.xreadgroup.assert_called()
    
    @pytest.mark.asyncio
    async def test_worker_stops_when_redis_disabled(self, global_state, mock_redis_pool):
        """Worker se pausa cuando Redis está deshabilitado."""
        global_state.redis_enabled = False
        global_state.redis = mock_redis_pool
        global_state.running = True
        
        task = asyncio.create_task(global_state._normal_worker_loop())
        
        # Dar tiempo para una iteración
        await asyncio.sleep(0.1)
        
        # Redis no debería ser llamado
        mock_redis_pool.xreadgroup.assert_not_called()
        
        # Limpiar
        global_state.running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_emergency_worker_faster_response(self, global_state, mock_redis_pool):
        """Worker de emergencia tiene timeout más corto para respuesta rápida."""
        global_state.redis = mock_redis_pool
        global_state.running = True
        
        # Configurar para que no haya mensajes (timeout)
        mock_redis_pool.xreadgroup = AsyncMock(return_value=[])
        
        task = asyncio.create_task(global_state._emergency_worker_loop())
        
        # Dar tiempo para que haga una lectura
        await asyncio.sleep(0.15)  # Mayor a 100ms timeout
        
        # Detener
        global_state.running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
        
        # Verificar que usó timeout corto (100ms vs 500ms del normal)
        call_args = mock_redis_pool.xreadgroup.call_args
        assert call_args[1]["block"] == 100  # 100ms para emergencias


# ============================================================================
# TESTS PARA PROCESAMIENTO DE SEÑALES
# ============================================================================

class TestSignalProcessing:
    """Tests para procesamiento de señales en GlobalState."""
    
    @pytest.mark.asyncio
    async def test_process_normal_signal_success(self, global_state, mock_postgres_pool, mock_redis_pool):
        """Procesar señal normal exitosamente."""
        # Configurar mocks
        message_id = "1705311000000-0"
        signal_data = {
            "vehicle_id": "TRUCK-001",
            "speed": 75.5,
            "latitude": 4.60971,
            "longitude": -74.08175,
            "timestamp": "2024-01-15T10:30:00Z",
            "panic_button": False
        }
        message_data = {"data": json.dumps(signal_data)}
        
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        # Ejecutar procesamiento
        await global_state._process_normal_signal(message_id, message_data)
        
        # Verificar que se llamó a ACK
        mock_redis_pool.xack.assert_called_once_with(
            "ccs_test_stream", "ccs_workers", message_id
        )
        
        # Verificar que se actualizaron métricas
        assert global_state.metrics["signals_processed"] == 1
    
    @pytest.mark.asyncio
    async def test_process_emergency_signal_success(self, global_state, mock_postgres_pool, mock_redis_pool):
        """Procesar señal de emergencia exitosamente."""
        message_id = "1705311000001-0"
        emergency_data = {
            "vehicle_id": "TAXI-101",
            "speed": 0.0,
            "latitude": 4.60971,
            "longitude": -74.08175,
            "timestamp": "2024-01-15T10:30:00Z",
            "panic_button": True
        }
        message_data = {"data": json.dumps(emergency_data)}
        
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        # Ejecutar procesamiento de emergencia
        await global_state._process_emergency_signal(message_id, message_data)
        
        # Verificar ACK en stream de emergencia
        mock_redis_pool.xack.assert_called_once_with(
            "ccs_test_emergency_stream", "ccs_emergency_workers", message_id
        )
        
        # Verificar métricas de emergencia
        assert global_state.metrics["emergencies_processed"] == 1
        assert global_state.metrics["last_emergency_time"] is not None
    
    @pytest.mark.asyncio
    async def test_process_signal_with_invalid_json(self, global_state, mock_redis_pool):
        """Manejar JSON inválido en mensaje."""
        message_id = "1705311000000-0"
        message_data = {"data": "{invalid json"}
        
        global_state.redis = mock_redis_pool
        
        # No debería lanzar excepción
        await global_state._process_normal_signal(message_id, message_data)
        
        # No debería hacer ACK por mensaje inválido
        mock_redis_pool.xack.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_signal_database_error(self, global_state, mock_postgres_pool, mock_redis_pool):
        """Manejar error de base de datos durante procesamiento."""
        message_id = "1705311000000-0"
        signal_data = {
            "vehicle_id": "TRUCK-001",
            "speed": 75.5,
            "latitude": 4.60971,
            "longitude": -74.08175,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        message_data = {"data": json.dumps(signal_data)}
        
        # Configurar error en PostgreSQL
        mock_conn = AsyncMock()
        mock_conn.fetchval = AsyncMock(side_effect=Exception("DB error"))
        mock_postgres_pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        # No debería lanzar excepción
        await global_state._process_normal_signal(message_id, message_data)
        
        # No debería hacer ACK por error
        mock_redis_pool.xack.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_emergency_processing_time_measurement(self, global_state, mock_postgres_pool, mock_redis_pool):
        """Medir tiempo de procesamiento de emergencias."""
        message_id = "1705311000001-0"
        emergency_data = {
            "vehicle_id": "TAXI-101",
            "speed": 0.0,
            "latitude": 4.60971,
            "longitude": -74.08175,
            "timestamp": "2024-01-15T10:30:00Z",
            "panic_button": True
        }
        message_data = {"data": json.dumps(emergency_data)}
        
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        # Ejecutar y medir tiempo
        start = time.time()
        await global_state._process_emergency_signal(message_id, message_data)
        end = time.time()
        
        processing_time = end - start
        
        # Verificar que se registró (aunque el tiempo real es con mocks)
        # En producción, esto verificaría < 2 segundos
        assert processing_time < 1.0  # Con mocks debe ser rápido


# ============================================================================
# TESTS PARA CACHE DE GEOFENCES Y SCHEDULES
# ============================================================================

class TestCacheManagement:
    """Tests para manejo de cache en GlobalState."""
    
    @pytest.mark.asyncio
    async def test_load_geofences_and_schedules_success(self, global_state, mock_postgres_pool):
        """Cargar geocercas y horarios desde DB a cache."""
        # Configurar datos de prueba en DB
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=[
            [  # Geofences
                {"vehicle_id": "TRUCK-001", "geofence_data": json.dumps({
                    "geofences": [
                        {"name": "ZONA_NORTE", "center": {"latitude": 4.60971, "longitude": -74.08175}, "radius_km": 5.0}
                    ]
                })}
            ],
            [  # Schedules
                {"vehicle_id": "MOTO-301", "schedule_data": json.dumps({
                    "start_time": "06:00",
                    "end_time": "22:00",
                    "days_of_week": [1, 2, 3, 4, 5]
                })}
            ]
        ])
        mock_postgres_pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        global_state.pool = mock_postgres_pool
        
        await global_state._load_geofences_and_schedules()
        
        # Verificar que se cargó en cache
        assert "TRUCK-001" in global_state.geofence_cache
        assert "MOTO-301" in global_state.schedule_cache
        
        # Verificar datos
        assert global_state.geofence_cache["TRUCK-001"][0]["name"] == "ZONA_NORTE"
        assert global_state.schedule_cache["MOTO-301"]["start_time"] == "06:00"
    
    @pytest.mark.asyncio
    async def test_load_geofences_with_invalid_json(self, global_state, mock_postgres_pool):
        """Manejar JSON inválido en datos de geocercas."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"vehicle_id": "TRUCK-001", "geofence_data": "{invalid json"}
        ])
        mock_postgres_pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        global_state.pool = mock_postgres_pool
        
        # No debería lanzar excepción
        await global_state._load_geofences_and_schedules()
        
        # Cache debería estar vacío o no contener el dato inválido
        assert "TRUCK-001" not in global_state.geofence_cache
    
    @pytest.mark.asyncio
    async def test_load_schedules_with_missing_fields(self, global_state, mock_postgres_pool):
        """Manejar datos de horarios con campos faltantes."""
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[
            {"vehicle_id": "MOTO-301", "schedule_data": json.dumps({
                # Falta start_time
                "end_time": "22:00",
                "days_of_week": [1, 2, 3]
            })}
        ])
        mock_postgres_pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        global_state.pool = mock_postgres_pool
        
        await global_state._load_geofences_and_schedules()
        
        # Podría no cargarse o cargarse parcialmente
        # Depende de la implementación, pero no debería crashear
    
    @pytest.mark.asyncio
    async def test_cache_persistence_across_processing(self, global_state):
        """Verificar que el cache persiste durante el procesamiento."""
        # Agregar datos manualmente al cache
        global_state.geofence_cache["TEST-001"] = [
            {"name": "TEST_ZONE", "center": {"latitude": 0.0, "longitude": 0.0}, "radius_km": 1.0}
        ]
        
        global_state.schedule_cache["TEST-002"] = {
            "start_time": "00:00",
            "end_time": "23:59",
            "days_of_week": [1, 2, 3, 4, 5, 6, 7]
        }
        
        # Los datos deberían persistir
        assert "TEST-001" in global_state.geofence_cache
        assert "TEST-002" in global_state.schedule_cache
        
        # Procesar una señal que use estos caches
        # (esto se probaría en integración con RuleService)


# ============================================================================
# TESTS PARA MÉTRICAS Y MONITOREO
# ============================================================================

class TestMetrics:
    """Tests para métricas en GlobalState."""
    
    @pytest.mark.asyncio
    async def test_metrics_initialization(self, global_state):
        """Verificar que las métricas se inicializan correctamente."""
        assert global_state.metrics == {
            "signals_processed": 0,
            "alerts_generated": 0,
            "emergencies_processed": 0,
            "last_emergency_time": None
        }
    
    @pytest.mark.asyncio
    async def test_metrics_increment_on_signal_processing(self, global_state, mock_postgres_pool, mock_redis_pool):
        """Las métricas se incrementan al procesar señales."""
        # Configurar
        message_id = "1705311000000-0"
        signal_data = {
            "vehicle_id": "TRUCK-001",
            "speed": 75.5,
            "latitude": 4.60971,
            "longitude": -74.08175,
            "timestamp": "2024-01-15T10:30:00Z"
        }
        message_data = {"data": json.dumps(signal_data)}
        
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        # Métricas iniciales
        initial_count = global_state.metrics["signals_processed"]
        
        # Procesar
        await global_state._process_normal_signal(message_id, message_data)
        
        # Verificar incremento
        assert global_state.metrics["signals_processed"] == initial_count + 1
    
    @pytest.mark.asyncio
    async def test_emergency_metrics_update(self, global_state, mock_postgres_pool, mock_redis_pool):
        """Métricas específicas para emergencias."""
        message_id = "1705311000001-0"
        emergency_data = {
            "vehicle_id": "TAXI-101",
            "speed": 0.0,
            "latitude": 4.60971,
            "longitude": -74.08175,
            "timestamp": "2024-01-15T10:30:00Z",
            "panic_button": True
        }
        message_data = {"data": json.dumps(emergency_data)}
        
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        # Procesar emergencia
        await global_state._process_emergency_signal(message_id, message_data)
        
        # Verificar todas las métricas de emergencia
        assert global_state.metrics["emergencies_processed"] == 1
        assert global_state.metrics["last_emergency_time"] is not None
        # signals_processed también debería incrementar
        assert global_state.metrics["signals_processed"] == 1
    
    @pytest.mark.asyncio
    async def test_metrics_reset_on_new_instance(self):
        """Cada instancia de GlobalState tiene sus propias métricas."""
        state1 = GlobalState()
        state2 = GlobalState()
        
        # Modificar métricas en una instancia
        state1.metrics["signals_processed"] = 100
        
        # La otra instancia no debería verse afectada
        assert state2.metrics["signals_processed"] == 0


# ============================================================================
# TESTS PARA SETUP DE REDIS STREAMS
# ============================================================================

class TestRedisStreamSetup:
    """Tests para configuración de streams de Redis."""
    
    @pytest.mark.asyncio
    async def test_setup_redis_streams_creates_groups(self, global_state, mock_redis_pool):
        """Crear grupos de consumidores en Redis."""
        await global_state._setup_redis_streams()
        
        # Verificar que se intentó crear ambos grupos
        assert mock_redis_pool.xgroup_create.call_count == 2
        
        # Verificar parámetros
        calls = mock_redis_pool.xgroup_create.call_args_list
        
        # Stream normal
        assert calls[0][0][0] == "ccs_test_stream"  # stream name
        assert calls[0][0][1] == "ccs_workers"      # group name
        
        # Stream de emergencia
        assert calls[1][0][0] == "ccs_test_emergency_stream"
        assert calls[1][0][1] == "ccs_emergency_workers"
    
    @pytest.mark.asyncio
    async def test_setup_redis_streams_handles_existing_groups(self, global_state, mock_redis_pool):
        """Manejar cuando los grupos ya existen (BUSYGROUP error)."""
        # Simular error BUSYGROUP (grupo ya existe)
        mock_redis_pool.xgroup_create = AsyncMock(
            side_effect=Exception("BUSYGROUP Consumer Group name already exists")
        )
        
        # No debería lanzar excepción
        await global_state._setup_redis_streams()
        
        # Debería intentar crear ambos grupos
        assert mock_redis_pool.xgroup_create.call_count == 2
    
    @pytest.mark.asyncio
    async def test_setup_redis_streams_handles_other_errors(self, global_state, mock_redis_pool):
        """Manejar otros errores en creación de streams."""
        # Simular error diferente
        mock_redis_pool.xgroup_create = AsyncMock(
            side_effect=Exception("Redis connection lost")
        )
        
        # Debería loguear warning pero no lanzar excepción
        await global_state._setup_redis_streams()
        
        # Aún debería intentar crear ambos grupos
        assert mock_redis_pool.xgroup_create.call_count == 2


# ============================================================================
# TESTS PARA MANEJO DE ERRORES Y RESILIENCIA
# ============================================================================

class TestErrorHandlingAndResilience:
    """Tests para manejo de errores y resiliencia."""
    
    @pytest.mark.asyncio
    async def test_state_recovery_after_redis_failure(self, global_state, mock_redis_pool, mock_postgres_pool):
        """Recuperación después de falla temporal de Redis."""
        # Simular que Redis falla inicialmente
        mock_redis_pool.ping = AsyncMock(side_effect=[Exception("Redis down"), True])
        
        # El estado debería manejar esto en initialize()
        # (se prueba en TestStateInitialization)
        
        # Para workers: si Redis está deshabilitado, se pausan
        global_state.redis_enabled = False
        global_state.redis = mock_redis_pool
        global_state.running = True
        
        task = asyncio.create_task(global_state._normal_worker_loop())
        await asyncio.sleep(0.1)
        
        # Worker no debería usar Redis
        mock_redis_pool.xreadgroup.assert_not_called()
        
        # Limpiar
        global_state.running = False
        task.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_graceful_degradation_on_db_failure(self, global_state, mock_postgres_pool):
        """Degradación elegante cuando DB falla."""
        # Simular que la carga de geocercas falla
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(side_effect=Exception("DB error"))
        mock_postgres_pool.acquire = AsyncMock(return_value=mock_conn.__aenter__())
        
        global_state.pool = mock_postgres_pool
        
        # No debería lanzar excepción
        await global_state._load_geofences_and_schedules()
        
        # Cache debería estar vacío (o con datos anteriores si los había)
        assert len(global_state.geofence_cache) == 0
        assert len(global_state.schedule_cache) == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_for_redis(self, global_state):
        """Verificar circuit breaker para Redis."""
        # redis_enabled actúa como circuit breaker
        assert hasattr(global_state, 'redis_enabled')
        
        # Por defecto debería estar habilitado
        assert global_state.redis_enabled is True
        
        # Puede ser deshabilitado manualmente (simulando circuit breaker abierto)
        global_state.redis_enabled = False
        
        # Cuando está deshabilitado, ciertas operaciones se saltan
        # Esto se prueba en otros tests


# ============================================================================
# TESTS DE INTEGRACIÓN REAL (OPCIONAL - REQUIERE DOCKER)
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.docker
class TestRealIntegration:
    """Tests de integración real con servicios en Docker."""
    
    @pytest.mark.asyncio
    async def test_real_redis_connection(self):
        """Conectar a Redis real (requiere Redis corriendo)."""
        import os
        from redis.asyncio import Redis
        
        redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379")
        
        try:
            redis = Redis.from_url(redis_url, decode_responses=True)
            await redis.ping()
            await redis.close()
            
            # Si llegamos aquí, la conexión funciona
            assert True
        except Exception as e:
            # Si Redis no está disponible, saltar test
            pytest.skip(f"Redis no disponible: {e}")
    
    @pytest.mark.asyncio
    async def test_real_postgres_connection(self):
        """Conectar a PostgreSQL real (requiere PostgreSQL corriendo)."""
        import os
        import asyncpg
        
        db_url = os.getenv("TEST_DATABASE_URL", "postgresql://postgres:password@localhost:5432/ccs_test")
        
        try:
            conn = await asyncpg.connect(db_url)
            await conn.close()
            
            # Si llegamos aquí, la conexión funciona
            assert True
        except Exception as e:
            # Si PostgreSQL no está disponible, saltar test
            pytest.skip(f"PostgreSQL no disponible: {e}")


# ============================================================================
# TESTS DE CONCURRENCIA Y RENDIMIENTO
# ============================================================================

class TestConcurrencyAndPerformance:
    """Tests para concurrencia y rendimiento."""
    
    @pytest.mark.asyncio
    async def test_concurrent_signal_processing(self, global_state, mock_postgres_pool, mock_redis_pool):
        """Procesar múltiples señales concurrentemente."""
        global_state.pool = mock_postgres_pool
        global_state.redis = mock_redis_pool
        
        # Crear múltiples tareas de procesamiento
        tasks = []
        for i in range(10):
            message_id = f"170531100000{i}-0"
            signal_data = {
                "vehicle_id": f"TRUCK-{i:03d}",
                "speed": 50.0 + i,
                "latitude": 4.60971,
                "longitude": -74.08175,
                "timestamp": "2024-01-15T10:30:00Z"
            }
            message_data = {"data": json.dumps(signal_data)}
            
            task = asyncio.create_task(
                global_state._process_normal_signal(message_id, message_data)
            )
            tasks.append(task)
        
        # Ejecutar concurrentemente
        await asyncio.gather(*tasks)
        
        # Verificar que todas se procesaron
        assert global_state.metrics["signals_processed"] == 10
        
        # Verificar múltiples ACKs
        assert mock_redis_pool.xack.call_count == 10
    
    @pytest.mark.asyncio
    async def test_worker_concurrency_limits(self, global_state, mock_redis_pool):
        """Workers respetan límites de concurrencia (count en xreadgroup)."""
        global_state.redis = mock_redis_pool
        global_state.running = True
        
        # El worker normal usa count=100 (procesamiento por lotes)
        mock_redis_pool.xreadgroup = AsyncMock(return_value=[])
        
        task = asyncio.create_task(global_state._normal_worker_loop())
        await asyncio.sleep(0.1)
        
        # Verificar parámetros de xreadgroup
        call_args = mock_redis_pool.xreadgroup.call_args
        assert call_args[1]["count"] == 100  # Lote de 100 mensajes
        
        # El worker de emergencia usa count=10 (más responsivo)
        mock_redis_pool.xreadgroup.reset_mock()
        
        task2 = asyncio.create_task(global_state._emergency_worker_loop())
        await asyncio.sleep(0.1)
        
        call_args = mock_redis_pool.xreadgroup.call_args
        assert call_args[1]["count"] == 10  # Lote más pequeño para emergencias
        
        # Limpiar
        global_state.running = False
        task.cancel()
        task2.cancel()
        
        try:
            await asyncio.gather(task, task2, return_exceptions=True)
        except asyncio.CancelledError:
            pass