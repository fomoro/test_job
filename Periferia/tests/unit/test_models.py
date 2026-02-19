"""
tests/unit/test_models.py - Tests unitarios para modelos Pydantic del dominio

Responsabilidades:
- Validar que los modelos Pydantic funcionan correctamente
- Verificar validaciones de datos
- Testear métodos custom como to_json_serializable_dict()
- Cubrir enums y constantes

Características:
- @pytest.mark.unit: Tests rápidos, sin dependencias
- Sin mocks de base de datos o Redis
- Sin lógica de negocio compleja
"""

import json
from datetime import datetime, time
import pytest

# Importar solo modelos, no servicios
from domain.models import (
    Signal, Location, Geofence, TimeSchedule,
    RuleUpdate, GeofenceDefinition, ScheduleDefinition,
    HealthResponse, SignalResponse,
    VehicleType, RuleType, ActionType
)


# ============================================================================
# TESTS BÁSICOS - ENUMS
# ============================================================================

class TestEnums:
    """Tests para enums del dominio."""
    
    def test_vehicle_type_enum_values(self):
        """Verificar valores de VehicleType."""
        assert VehicleType.TRUCK.value == "TRUCK"
        assert VehicleType.CAR.value == "CAR"
        assert VehicleType.MOTO.value == "MOTO"
    
    def test_vehicle_type_enum_members(self):
        """Verificar miembros de VehicleType."""
        assert list(VehicleType) == [VehicleType.TRUCK, VehicleType.CAR, VehicleType.MOTO]
    
    def test_rule_type_enum_has_correct_values(self):
        """Verificar que RuleType tiene todos los tipos de reglas."""
        expected = {"MAX_SPEED", "PANIC_BUTTON", "MAX_TEMP", "MIN_TEMP", 
                   "GEOFENCE_EXIT", "SCHEDULE", "UNPLANNED_STOP", "DOOR_SENSOR"}
        actual = {rt.value for rt in RuleType}
        assert actual == expected
    
    def test_action_type_enum_has_correct_values(self):
        """Verificar que ActionType tiene todas las acciones."""
        expected = {"NOTIFY_POLICE", "NOTIFY_OWNER", "SMS_OWNER", 
                   "LOG_ONLY", "CALL_EMERGENCY", "NOTIFY_SECURITY"}
        actual = {at.value for at in ActionType}
        assert actual == expected


# ============================================================================
# TESTS BÁSICOS - MODELO SIGNAL
# ============================================================================

class TestSignalModel:
    """Tests para el modelo Signal (señal de vehículo)."""
    
    def test_create_signal_with_minimal_data(self):
        """Crear señal con datos mínimos requeridos."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=4.60971,
            longitude=-74.08175
        )
        
        assert signal.vehicle_id == "TEST-001"
        assert signal.speed == 50.0
        assert signal.latitude == 4.60971
        assert signal.longitude == -74.08175
        assert signal.panic_button is False  # default
        assert signal.temperature is None  # default
        assert signal.vehicle_type is None  # default
        assert signal.metadata == {}  # default
        assert isinstance(signal.timestamp, datetime)  # auto-generado
    
    def test_create_signal_with_all_fields(self):
        """Crear señal con todos los campos."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        signal = Signal(
            vehicle_id="TRUCK-011",
            speed=65.5,
            latitude=4.60971,
            longitude=-74.08175,
            timestamp=timestamp,
            panic_button=False,
            temperature=-15.0,
            vehicle_type=VehicleType.TRUCK,
            metadata={"cargo_type": "pharmaceuticals", "door_status": "closed"}
        )
        
        assert signal.vehicle_id == "TRUCK-011"
        assert signal.speed == 65.5
        assert signal.timestamp == timestamp
        assert signal.vehicle_type == VehicleType.TRUCK
        assert signal.metadata["cargo_type"] == "pharmaceuticals"
    
    def test_signal_vehicle_id_validation_min_length(self):
        """Validar que vehicle_id no puede estar vacío."""
        with pytest.raises(ValueError) as exc:
            Signal(
                vehicle_id="",  # vacío
                speed=50.0,
                latitude=0.0,
                longitude=0.0
            )
        assert "vehicle_id" in str(exc.value)
    
    def test_signal_vehicle_id_validation_max_length(self):
        """Validar que vehicle_id no puede exceder 20 caracteres."""
        with pytest.raises(ValueError):
            Signal(
                vehicle_id="A" * 21,  # 21 caracteres
                speed=50.0,
                latitude=0.0,
                longitude=0.0
            )
    
    def test_signal_speed_cannot_be_negative(self):
        """Validar que speed no puede ser negativo."""
        with pytest.raises(ValueError):
            Signal(
                vehicle_id="TEST-001",
                speed=-10.0,  # negativo
                latitude=0.0,
                longitude=0.0
            )
    
    def test_signal_temperature_absolute_zero_limit(self):
        """Validar que temperatura no puede ser menor al cero absoluto."""
        with pytest.raises(ValueError):
            Signal(
                vehicle_id="TEST-001",
                speed=50.0,
                latitude=0.0,
                longitude=0.0,
                temperature=-274.0  # menor a -273.15°C
            )
    
    def test_signal_to_json_serializable_dict_converts_datetime(self):
        """Verificar que timestamp se convierte a string ISO."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0,
            timestamp=timestamp
        )
        
        result = signal.to_json_serializable_dict()
        
        assert isinstance(result["timestamp"], str)
        assert result["timestamp"] == "2024-01-15T10:30:00"
    
    def test_signal_to_json_serializable_dict_converts_enum(self):
        """Verificar que enums se convierten a strings."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0,
            vehicle_type=VehicleType.TRUCK
        )
        
        result = signal.to_json_serializable_dict()
        
        assert result["vehicle_type"] == "TRUCK"
        assert isinstance(result["vehicle_type"], str)
    
    def test_signal_to_json_serializable_dict_without_vehicle_type(self):
        """Verificar conversión cuando vehicle_type es None."""
        signal = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=0.0,
            longitude=0.0
            # vehicle_type no especificado
        )
        
        result = signal.to_json_serializable_dict()
        
        assert result["vehicle_type"] is None


# ============================================================================
# TESTS BÁSICOS - MODELO LOCATION
# ============================================================================

class TestLocationModel:
    """Tests para el modelo Location (ubicación geográfica)."""
    
    def test_create_valid_location(self):
        """Crear ubicación válida."""
        location = Location(latitude=4.60971, longitude=-74.08175)
        
        assert location.latitude == 4.60971
        assert location.longitude == -74.08175
    
    def test_location_latitude_bounds(self):
        """Validar límites de latitud (-90 a 90)."""
        # Límite inferior
        location = Location(latitude=-90.0, longitude=0.0)
        assert location.latitude == -90.0
        
        # Límite superior
        location = Location(latitude=90.0, longitude=0.0)
        assert location.latitude == 90.0
        
        # Fuera de límites
        with pytest.raises(ValueError):
            Location(latitude=-91.0, longitude=0.0)
        
        with pytest.raises(ValueError):
            Location(latitude=91.0, longitude=0.0)
    
    def test_location_longitude_bounds(self):
        """Validar límites de longitud (-180 a 180)."""
        # Límite inferior
        location = Location(latitude=0.0, longitude=-180.0)
        assert location.longitude == -180.0
        
        # Límite superior
        location = Location(latitude=0.0, longitude=180.0)
        assert location.longitude == 180.0
        
        # Fuera de límites
        with pytest.raises(ValueError):
            Location(latitude=0.0, longitude=-181.0)
        
        with pytest.raises(ValueError):
            Location(latitude=0.0, longitude=181.0)


# ============================================================================
# TESTS BÁSICOS - MODELO GEOFENCE
# ============================================================================

class TestGeofenceModel:
    """Tests para el modelo Geofence (geocerca)."""
    
    def test_create_valid_geofence(self):
        """Crear geocerca válida."""
        geofence = Geofence(
            name="Zona_Norte_Bogota",
            center=Location(latitude=4.60971, longitude=-74.08175),
            radius_km=5.0
        )
        
        assert geofence.name == "Zona_Norte_Bogota"
        assert geofence.center.latitude == 4.60971
        assert geofence.radius_km == 5.0
        assert geofence.is_allowed is True  # default
    
    def test_geofence_name_length_validation(self):
        """Validar longitud del nombre (1-50 caracteres)."""
        # Nombre muy corto
        with pytest.raises(ValueError):
            Geofence(
                name="",
                center=Location(latitude=0.0, longitude=0.0),
                radius_km=1.0
            )
        
        # Nombre muy largo
        with pytest.raises(ValueError):
            Geofence(
                name="A" * 51,
                center=Location(latitude=0.0, longitude=0.0),
                radius_km=1.0
            )
        
        # Nombre válido en límite
        geofence = Geofence(
            name="A" * 50,  # 50 caracteres (máximo)
            center=Location(latitude=0.0, longitude=0.0),
            radius_km=1.0
        )
        assert len(geofence.name) == 50
    
    def test_geofence_radius_must_be_positive(self):
        """Validar que el radio debe ser positivo."""
        with pytest.raises(ValueError):
            Geofence(
                name="Test",
                center=Location(latitude=0.0, longitude=0.0),
                radius_km=0.0  # no positivo
            )
        
        with pytest.raises(ValueError):
            Geofence(
                name="Test",
                center=Location(latitude=0.0, longitude=0.0),
                radius_km=-5.0  # negativo
            )
    
    def test_geofence_is_allowed_can_be_false(self):
        """Verificar que is_allowed puede ser False."""
        geofence = Geofence(
            name="Zona_Prohibida",
            center=Location(latitude=0.0, longitude=0.0),
            radius_km=10.0,
            is_allowed=False
        )
        
        assert geofence.is_allowed is False


# ============================================================================
# TESTS BÁSICOS - MODELO TIMESCHEDULE
# ============================================================================

class TestTimeScheduleModel:
    """Tests para el modelo TimeSchedule (horario)."""
    
    def test_create_valid_schedule(self):
        """Crear horario válido."""
        schedule = TimeSchedule(
            start_time="06:00",
            end_time="22:00",
            days_of_week=[1, 2, 3, 4, 5]  # Lunes a Viernes
        )
        
        assert schedule.start_time == "06:00"
        assert schedule.end_time == "22:00"
        assert schedule.days_of_week == [1, 2, 3, 4, 5]
    
    def test_schedule_defaults_to_all_days(self):
        """Verificar que por defecto incluye todos los días."""
        schedule = TimeSchedule(start_time="00:00", end_time="23:59")
        
        assert schedule.days_of_week == [1, 2, 3, 4, 5, 6, 7]  # Todos los días
    
    def test_schedule_time_format_validation(self):
        """Validar formato de hora HH:MM."""
        # Formatos inválidos
        invalid_times = ["25:00", "12:60", "not-time", "12:30:45", "12"]
        
        for invalid_time in invalid_times:
            with pytest.raises(ValueError):
                TimeSchedule(start_time=invalid_time, end_time="22:00")
            
            with pytest.raises(ValueError):
                TimeSchedule(start_time="06:00", end_time=invalid_time)
    
    def test_schedule_days_of_week_validation(self):
        """Validar días de la semana (1-7)."""
        # Días inválidos
        with pytest.raises(ValueError):
            TimeSchedule(
                start_time="06:00",
                end_time="22:00",
                days_of_week=[0, 1, 2]  # 0 no es válido
            )
        
        with pytest.raises(ValueError):
            TimeSchedule(
                start_time="06:00",
                end_time="22:00",
                days_of_week=[1, 8, 3]  # 8 no es válido
            )
        
        # Días válidos
        schedule = TimeSchedule(
            start_time="06:00",
            end_time="22:00",
            days_of_week=[1, 7]  # Lunes y Domingo
        )
        assert schedule.days_of_week == [1, 7]


# ============================================================================
# TESTS BÁSICOS - MODELOS DE DEFINICIÓN
# ============================================================================

class TestDefinitionModels:
    """Tests para modelos de definición (RuleUpdate, GeofenceDefinition, etc.)."""
    
    def test_rule_update_model(self):
        """Test para modelo RuleUpdate."""
        rule_update = RuleUpdate(
            vehicle_id="TRUCK-001",
            rule_type=RuleType.MAX_SPEED,
            comparison_value="90.0",
            action_type=ActionType.NOTIFY_OWNER
        )
        
        assert rule_update.vehicle_id == "TRUCK-001"
        assert rule_update.rule_type == RuleType.MAX_SPEED
        assert rule_update.comparison_value == "90.0"
        assert rule_update.action_type == ActionType.NOTIFY_OWNER
        assert rule_update.is_active is True  # default
    
    def test_geofence_definition_model(self):
        """Test para modelo GeofenceDefinition."""
        geofence_def = GeofenceDefinition(
            vehicle_id="TRUCK-001",
            geofence=Geofence(
                name="Zona_Norte",
                center=Location(latitude=4.60971, longitude=-74.08175),
                radius_km=5.0
            )
        )
        
        assert geofence_def.vehicle_id == "TRUCK-001"
        assert geofence_def.geofence.name == "Zona_Norte"
    
    def test_schedule_definition_model(self):
        """Test para modelo ScheduleDefinition."""
        schedule_def = ScheduleDefinition(
            vehicle_id="MOTO-301",
            schedule=TimeSchedule(
                start_time="06:00",
                end_time="22:00",
                days_of_week=[1, 2, 3, 4, 5]
            )
        )
        
        assert schedule_def.vehicle_id == "MOTO-301"
        assert schedule_def.schedule.start_time == "06:00"


# ============================================================================
# TESTS BÁSICOS - MODELOS DE RESPUESTA
# ============================================================================

class TestResponseModels:
    """Tests para modelos de respuesta API."""
    
    def test_health_response_model(self):
        """Test para modelo HealthResponse."""
        timestamp = datetime.utcnow()
        health_response = HealthResponse(
            status="healthy",
            services={"postgresql": "healthy", "redis": "healthy"},
            uptime_seconds=3600.5,
            timestamp=timestamp,
            metrics={"signals_processed": 1500}
        )
        
        assert health_response.status == "healthy"
        assert health_response.services["redis"] == "healthy"
        assert health_response.uptime_seconds == 3600.5
        assert health_response.timestamp == timestamp
        assert health_response.metrics["signals_processed"] == 1500
    
    def test_health_response_without_metrics(self):
        """HealthResponse puede no incluir métricas."""
        health_response = HealthResponse(
            status="degraded",
            services={"postgresql": "unhealthy"},
            uptime_seconds=100.0,
            timestamp=datetime.utcnow()
        )
        
        assert health_response.metrics is None
    
    def test_signal_response_model(self):
        """Test para modelo SignalResponse."""
        timestamp = datetime.utcnow()
        signal_response = SignalResponse(
            status="accepted",
            vehicle_id="TRUCK-001",
            message_id="1705311000000-0",
            processing_time_ms=45.2,
            timestamp=timestamp,
            priority="normal"
        )
        
        assert signal_response.status == "accepted"
        assert signal_response.vehicle_id == "TRUCK-001"
        assert signal_response.processing_time_ms == 45.2
        assert signal_response.priority == "normal"


# ============================================================================
# TESTS DE SERIALIZACIÓN/DESERIALIZACIÓN
# ============================================================================

class TestSerialization:
    """Tests para serialización/deserialización de modelos."""
    
    def test_signal_json_roundtrip(self):
        """Verificar que Signal puede serializarse a JSON y parsearse de vuelta."""
        original = Signal(
            vehicle_id="TEST-001",
            speed=50.0,
            latitude=4.60971,
            longitude=-74.08175,
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            vehicle_type=VehicleType.TRUCK,
            metadata={"test": "data"}
        )
        
        # Serializar
        json_dict = original.to_json_serializable_dict()
        json_str = json.dumps(json_dict)
        
        # Parsear
        parsed_dict = json.loads(json_str)
        
        # Reconstruir (timestamp necesita parsing)
        parsed_dict["timestamp"] = datetime.fromisoformat(
            parsed_dict["timestamp"].replace('Z', '+00:00')
        )
        if parsed_dict["vehicle_type"]:
            parsed_dict["vehicle_type"] = VehicleType(parsed_dict["vehicle_type"])
        
        reconstructed = Signal(**parsed_dict)
        
        # Comparar
        assert reconstructed.vehicle_id == original.vehicle_id
        assert reconstructed.speed == original.speed
        assert reconstructed.latitude == original.latitude
        assert reconstructed.longitude == original.longitude
        # Nota: microsegundos pueden diferir en timestamp
    
    def test_geofence_definition_dict_roundtrip(self):
        """Verificar que GeofenceDefinition puede convertirse a dict y volver."""
        original = GeofenceDefinition(
            vehicle_id="TRUCK-001",
            geofence=Geofence(
                name="Test",
                center=Location(latitude=10.0, longitude=20.0),
                radius_km=5.0,
                is_allowed=False
            )
        )
        
        # A dict
        as_dict = original.dict()
        
        # De dict a objeto
        reconstructed = GeofenceDefinition(**as_dict)
        
        assert reconstructed.vehicle_id == original.vehicle_id
        assert reconstructed.geofence.name == original.geofence.name
        assert reconstructed.geofence.center.latitude == original.geofence.center.latitude
        assert reconstructed.geofence.is_allowed == original.geofence.is_allowed


# ============================================================================
# TESTS DE CASOS BORDE
# ============================================================================

class TestEdgeCases:
    """Tests para casos extremos y límites."""
    
    def test_signal_at_coordinate_limits(self):
        """Señal en los límites de coordenadas."""
        # Polo Norte
        signal = Signal(
            vehicle_id="ARCTIC-01",
            speed=0.0,
            latitude=90.0,
            longitude=0.0
        )
        assert signal.latitude == 90.0
        
        # Polo Sur
        signal = Signal(
            vehicle_id="ANTARCTIC-01",
            speed=0.0,
            latitude=-90.0,
            longitude=0.0
        )
        assert signal.latitude == -90.0
        
        # Línea internacional de fecha
        signal = Signal(
            vehicle_id="DATE-LINE-01",
            speed=0.0,
            latitude=0.0,
            longitude=180.0
        )
        assert signal.longitude == 180.0
    
    def test_signal_with_maximum_speed(self):
        """Señal con velocidad máxima (aunque no hay límite técnico)."""
        signal = Signal(
            vehicle_id="RACER-01",
            speed=9999.9,  # Velocidad muy alta
            latitude=0.0,
            longitude=0.0
        )
        assert signal.speed == 9999.9
    
    def test_geofence_with_large_radius(self):
        """Geocerca con radio muy grande."""
        geofence = Geofence(
            name="Large_Area",
            center=Location(latitude=0.0, longitude=0.0),
            radius_km=10000.0  # 10,000 km
        )
        assert geofence.radius_km == 10000.0
    
    def test_schedule_crossing_midnight(self):
        """Horario que cruza la medianoche."""
        schedule = TimeSchedule(
            start_time="22:00",
            end_time="06:00",  # Cruza medianoche
            days_of_week=[1, 2, 3]
        )
        assert schedule.start_time == "22:00"
        assert schedule.end_time == "06:00"