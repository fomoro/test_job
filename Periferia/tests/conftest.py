"""
tests/conftest.py - Configuración global de pytest para CCS

Responsabilidades:
1. Configurar event loop para tests asíncronos
2. Definir fixtures compartidas para todos los tests
3. Configurar ambiente de testing
4. Proporcionar mocks y utilidades comunes
"""

import asyncio
import os
import sys
from datetime import datetime, time
from typing import Dict, Any, List, AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock, MagicMock, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Añadir el directorio app al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Cargar variables de entorno de testing
load_dotenv('.env.test')

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================

def pytest_configure(config):
    """Configuración inicial de pytest."""
    # Configurar marcadores personalizados
    config.addinivalue_line(
        "markers", "unit: Marca test como unitario (rápido, sin dependencias)"
    )
    config.addinivalue_line(
        "markers", "integration: Marca test como integración (lento, con dependencias)"
    )
    config.addinivalue_line(
        "markers", "slow: Marca test como lento (ej: tests de integración)"
    )
    config.addinivalue_line(
        "markers", "async: Marca test que requiere event loop asíncrono"
    )

# ============================================================================
# FIXTURES DE CONFIGURACIÓN ASYNCIO
# ============================================================================

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Crea un event loop para toda la sesión de tests.
    
    Necesario para tests asíncronos. Scope session para reutilizar el loop.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    
    yield loop
    
    # Limpiar
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()
    
    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()

# ============================================================================
# FIXTURES PARA UNIT TESTS (MOCKS)
# ============================================================================

@pytest.fixture
def mock_asyncpg_pool() -> AsyncMock:
    """
    Mock de asyncpg.Pool para tests unitarios.
    
    Simula conexiones a PostgreSQL sin necesidad de DB real.
    """
    pool = AsyncMock()
    
    # Configurar connection mock
    conn = AsyncMock()
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)
    conn.fetchval = AsyncMock(return_value=1)
    conn.execute = AsyncMock(return_value="INSERT 0 1")
    conn.executemany = AsyncMock(return_value=None)
    
    # Configurar pool para devolver connection mock
    pool.acquire = AsyncMock(return_value=conn.__aenter__())
    
    return pool

@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """
    Mock de Redis client para tests unitarios.
    
    Simula Redis sin necesidad de servidor real.
    """
    redis = AsyncMock()
    
    # Configurar métodos comunes
    redis.ping = AsyncMock(return_value=True)
    redis.get = AsyncMock(return_value=None)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    redis.xadd = AsyncMock(return_value="1705311000000-0")
    redis.xack = AsyncMock(return_value=1)
    redis.xreadgroup = AsyncMock(return_value=[])
    redis.xinfo_stream = AsyncMock(return_value={"length": 0})
    redis.xpending = AsyncMock(return_value={"pending": 0})
    redis.info = AsyncMock(return_value={"connected_clients": 1, "used_memory": 1000000})
    
    return redis

@pytest.fixture
def mock_global_state(mock_asyncpg_pool, mock_redis_client) -> Mock:
    """
    Mock completo de GlobalState para tests unitarios.
    """
    state = Mock()
    
    # Configurar atributos básicos
    state.pool = mock_asyncpg_pool
    state.redis = mock_redis_client
    state.redis_enabled = True
    state.running = True
    state.api_instance_id = "test-api-12345"
    state.start_time = datetime.utcnow()
    state.metrics = {
        "signals_processed": 0,
        "alerts_generated": 0,
        "emergencies_processed": 0,
        "last_emergency_time": None
    }
    state.geofence_cache = {}
    state.schedule_cache = {}
    
    # Configurar streams
    state.REDIS_STREAM_NAME = "ccs_signals_stream"
    state.EMERGENCY_STREAM_NAME = "ccs_emergency_stream"
    
    return state

# ============================================================================
# FIXTURES DE DATOS DE PRUEBA
# ============================================================================

@pytest.fixture
def sample_signal_data() -> Dict[str, Any]:
    """
    Datos de ejemplo para una señal de vehículo.
    
    Usado para crear objetos Signal en tests.
    """
    return {
        "vehicle_id": "TRUCK-001",
        "speed": 75.5,
        "latitude": 4.60971,
        "longitude": -74.08175,
        "timestamp": datetime.utcnow(),
        "panic_button": False,
        "temperature": -15.0,
        "vehicle_type": "TRUCK",
        "metadata": {
            "cargo_type": "general",
            "door_status": "closed"
        }
    }

@pytest.fixture
def sample_emergency_signal_data() -> Dict[str, Any]:
    """
    Datos de ejemplo para una señal de emergencia.
    """
    return {
        "vehicle_id": "TAXI-101",
        "speed": 0.0,
        "latitude": 4.60971,
        "longitude": -74.08175,
        "timestamp": datetime.utcnow(),
        "panic_button": True,  # ¡EMERGENCIA!
        "temperature": None,
        "vehicle_type": "CAR",
        "metadata": {}
    }

@pytest.fixture
def sample_rules_data() -> List[Dict[str, Any]]:
    """
    Datos de ejemplo para reglas activas.
    
    Simula respuesta de la base de datos.
    """
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
            "rule_type": "GEOFENCE_EXIT",
            "comparison_value": "ZONA_NORTE",
            "action_type": "NOTIFY_OWNER",
            "priority": 2
        }
    ]

@pytest.fixture
def sample_geofence_cache() -> Dict[str, List[Dict]]:
    """
    Datos de ejemplo para cache de geocercas.
    """
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
def sample_schedule_cache() -> Dict[str, Dict]:
    """
    Datos de ejemplo para cache de horarios.
    """
    return {
        "MOTO-301": {
            "start_time": "06:00",
            "end_time": "22:00",
            "days_of_week": [1, 2, 3, 4, 5]  # Lunes a Viernes
        }
    }

@pytest.fixture
def sample_owner_data() -> Dict[str, Any]:
    """
    Datos de ejemplo para propietario.
    
    Simula respuesta de la base de datos.
    """
    return {
        "id": "1001",
        "full_name": "Logística Nacional S.A.",
        "email": "flota@logistica-nal.com",
        "phone": "+576015550001"
    }

# ============================================================================
# FIXTURES PARA INTEGRATION TESTS (REALES)
# ============================================================================

@pytest.fixture(scope="session")
def test_database_url() -> str:
    """
    URL de base de datos para tests de integración.
    
    Por defecto usa variables de entorno, fallback a localhost.
    """
    return os.getenv("TEST_DATABASE_URL", "postgresql://postgres:password@localhost:5432/ccs_test")

@pytest.fixture(scope="session")
def test_redis_url() -> str:
    """
    URL de Redis para tests de integración.
    """
    return os.getenv("TEST_REDIS_URL", "redis://localhost:6379")

@pytest.fixture
def test_env_vars(test_database_url, test_redis_url) -> Dict[str, str]:
    """
    Variables de entorno para tests.
    
    Puede ser usado con patch.dict para modificar os.environ.
    """
    return {
        "DATABASE_URL": test_database_url,
        "REDIS_URL": test_redis_url,
        "REDIS_STREAM_NAME": "ccs_test_stream",
        "EMERGENCY_STREAM_NAME": "ccs_test_emergency_stream"
    }

# ============================================================================
# FIXTURES PARA API TESTS
# ============================================================================

@pytest.fixture
def test_client() -> TestClient:
    """
    TestClient de FastAPI para tests de endpoints HTTP.
    
    Nota: Necesita importar app desde main, pero lo hacemos lazy
    para evitar problemas de imports circulares.
    """
    from main import app
    return TestClient(app)

@pytest.fixture
def authenticated_test_client() -> TestClient:
    """
    TestClient con autenticación simulada.
    
    Para cuando implementes autenticación.
    """
    from main import app
    client = TestClient(app)
    # Configurar headers de autenticación aquí
    # client.headers.update({"Authorization": "Bearer test-token"})
    return client

# ============================================================================
# UTILIDADES Y HELPERS
# ============================================================================

@pytest.fixture
def frozen_time() -> datetime:
    """
    Retorna un timestamp congelado para tests.
    
    Útil para tests que dependen del tiempo actual.
    """
    return datetime(2024, 1, 15, 10, 30, 0)

@pytest.fixture
def mock_datetime_now(frozen_time):
    """
    Mock de datetime.now() y datetime.utcnow().
    
    Uso:
        with mock_datetime_now as mock_now:
            mock_now.now.return_value = frozen_time
            mock_now.utcnow.return_value = frozen_time
    """
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = frozen_time
        mock_datetime.utcnow.return_value = frozen_time
        yield mock_datetime

@pytest.fixture
def mock_time():
    """
    Mock de time para tests de horarios.
    """
    with patch('datetime.time') as mock_time:
        # Configurar time.fromisoformat para que funcione
        mock_time.fromisoformat.side_effect = time.fromisoformat
        yield mock_time

# ============================================================================
# FIXTURES PARA TEST DE REGLAS ESPECÍFICAS
# ============================================================================

@pytest.fixture
def speed_violation_signal() -> Dict[str, Any]:
    """Señal que viola límite de velocidad."""
    data = sample_signal_data()
    data["speed"] = 90.0  # Excede límite de 80
    return data

@pytest.fixture
def temperature_violation_signal() -> Dict[str, Any]:
    """Señal que viola temperatura."""
    data = sample_signal_data()
    data["temperature"] = -25.0  # Muy frío para límite de -18
    return data

@pytest.fixture
def geofence_violation_signal() -> Dict[str, Any]:
    """Señal fuera de geocerca."""
    data = sample_signal_data()
    data["latitude"] = 4.70000  # Fuera de radio de 5km
    data["longitude"] = -74.20000
    return data

@pytest.fixture
def schedule_violation_signal() -> Dict[str, Any]:
    """Señal en horario no permitido."""
    data = sample_signal_data()
    # Crear timestamp a las 23:00 (fuera de horario 06:00-22:00)
    data["timestamp"] = datetime(2024, 1, 15, 23, 0, 0)
    data["vehicle_id"] = "MOTO-301"  # Vehículo con horario restringido
    return data

# ============================================================================
# CONFIGURACIÓN DE LOGGING PARA TESTS
# ============================================================================

@pytest.fixture(autouse=True)
def setup_test_logging():
    """
    Configura logging para tests.
    
    Se ejecuta automáticamente en cada test.
    """
    import logging
    
    # Reducir verbosidad de logs en tests
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aioredis").setLevel(logging.WARNING)
    logging.getLogger("asyncpg").setLevel(logging.WARNING)
    
    # Capturar logs para assertions
    captured_logs = []
    
    class TestHandler(logging.Handler):
        def emit(self, record):
            captured_logs.append(record.getMessage())
    
    test_handler = TestHandler()
    logging.getLogger().addHandler(test_handler)
    
    yield captured_logs
    
    # Limpiar
    logging.getLogger().removeHandler(test_handler)

# ============================================================================
# MARCADORES Y CONFIGURACIÓN DE EJECUCIÓN
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """
    Modifica tests basado en marcadores.
    
    Permite saltar tests lentos con --skip-slow
    """
    skip_slow = config.getoption("--skip-slow")
    skip_integration = config.getoption("--skip-integration")
    
    for item in items:
        # Saltar tests lentos si se solicita
        if skip_slow and "slow" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Test lento omitido"))
        
        # Saltar tests de integración si se solicita
        if skip_integration and "integration" in item.keywords:
            item.add_marker(pytest.mark.skip(reason="Test de integración omitido"))
        
        # Marcar automáticamente tests async
        if "async" in item.keywords or "asyncio" in item.name:
            item.add_marker(pytest.mark.asyncio)

def pytest_addoption(parser):
    """Añadir opciones personalizadas a pytest."""
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Saltar tests marcados como 'slow'"
    )
    parser.addoption(
        "--skip-integration",
        action="store_true",
        default=False,
        help="Saltar tests de integración"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Ejecutar solo tests de integración"
    )

# ============================================================================
# CLEANUP Y TEARDOWN
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Limpieza automática después de cada test.
    
    Resetea mocks y estado compartido.
    """
    # Setup
    yield
    # Teardown
    # Limpiar patches y mocks globales si es necesario

# ============================================================================
# FIXTURES PARA COBERTURA DE CÓDIGO
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_coverage():
    """
    Configuración para reportes de cobertura.
    
    Se ejecuta una vez al inicio de la sesión.
    """
    # Aquí podrías configurar coverage.py si no usas pytest-cov
    yield
    # Generar reportes al final si es necesario