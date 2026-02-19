# Modelo Entidad-Relación - Base de Datos CCS

## Contexto
Diseño de base de datos escalable para el sistema de seguimiento vehicular CCS, soportando 500 señales por segundo, crecimiento del 20% anual, y consultas eficientes para procesamiento en tiempo real.

## Diagrama ER Completo

```mermaid
erDiagram
    OWNERS ||--o{ VEHICLES : "owns (1:N)"
    VEHICLES ||--o{ SIGNALS : "generates (1:N)"
    VEHICLES ||--o{ RULES : "has (1:N)"
    VEHICLES ||--o{ GEOFENCES : "defines (0:N)"
    VEHICLES ||--o{ SCHEDULES : "configures (0:N)"
    RULES ||--o{ ALERTS : "triggers (1:N)"
    SIGNALS ||--o{ ALERTS : "references (1:1)"
    OWNERS ||--o{ NOTIFICATIONS : "receives (1:N)"
    VEHICLES ||--o{ NOTIFICATIONS : "generates (1:N)"
    
    OWNERS {
        varchar id PK "OWN-001"
        varchar full_name "Juan Pérez"
        varchar email "juan@correo.com"
        varchar phone "+573001234567"
        varchar emergency_contact "+573001111111"
        boolean notifications_enabled true
        timestamp created_at "2024-01-01 00:00:00"
        timestamp updated_at "2024-01-15 10:30:00"
    }
    
    VEHICLES {
        varchar id PK "TRUCK-001"
        varchar owner_id FK
        enum type "TRUCK|CAR|MOTO"
        varchar license_plate "ABC123"
        varchar manufacturer "Volvo"
        varchar model "FH16"
        int manufacturing_year 2022
        boolean active true
        jsonb details "{\"company\":\"CCS\",\"color\":\"red\",\"fuel_type\":\"diesel\"}"
        timestamp created_at "2024-01-01"
        timestamp last_signal_at "2024-01-15 10:30:00"
    }
    
    RULES {
        serial id PK
        varchar vehicle_id FK
        enum rule_type "MAX_SPEED|PANIC_BUTTON|MAX_TEMP|MIN_TEMP|GEOFENCE_EXIT|SCHEDULE|UNPLANNED_STOP|DOOR_SENSOR"
        text comparison_value "80.5|-15.0|Zona_Norte"
        enum action_type "NOTIFY_POLICE|NOTIFY_OWNER|SMS_OWNER|LOG_ONLY|CALL_EMERGENCY|NOTIFY_SECURITY"
        boolean is_active true
        int priority 1
        jsonb metadata "{\"notification_channels\":[\"sms\",\"email\"]}"
        timestamp created_at "2024-01-01"
        timestamp updated_at "2024-01-15"
    }
    
    SIGNALS {
        bigserial id PK
        varchar vehicle_id FK
        timestamp timestamp "2024-01-15 10:30:00"
        double precision latitude 4.60971
        double precision longitude -74.08175
        real speed 65.5
        real heading 45.0
        real temperature -15.0
        boolean panic_button false
        jsonb metadata "{\"door_status\":\"closed\",\"engine_temp\":85.0,\"fuel_level\":65}"
        varchar api_instance "ccs-api-a1b2c3d4"
        timestamp processed_at "2024-01-15 10:30:05"
    }
    
    ALERTS {
        bigserial id PK
        varchar vehicle_id FK
        int rule_id FK
        bigint signal_id FK
        timestamp timestamp "2024-01-15 10:30:05"
        text message "Exceso velocidad: 85km/h > 80km/h"
        text action_taken "SMS enviado al dueño"
        enum status "generated|notified|resolved"
        jsonb details "{\"notified_to\":[\"owner\",\"police\"],\"response_time_ms\":1250}"
        timestamp resolved_at null
    }
    
    GEOFENCES {
        serial id PK
        varchar vehicle_id FK
        varchar name "Zona_Norte_Bogota"
        varchar description "Área de operación permitida"
        jsonb center "{\"latitude\":4.60971,\"longitude\":-74.08175}"
        double precision radius_km 5.0
        boolean is_allowed true
        jsonb polygon_coordinates null
        timestamp created_at "2024-01-01"
        timestamp active_until "2024-12-31"
    }
    
    SCHEDULES {
        serial id PK
        varchar vehicle_id FK
        varchar name "Horario_Laboral"
        time start_time "06:00:00"
        time end_time "22:00:00"
        int[] days_of_week "[1,2,3,4,5]"
        boolean active true
        timestamp created_at "2024-01-01"
        timestamp updated_at "2024-01-15"
    }
    
    NOTIFICATIONS {
        serial id PK
        varchar vehicle_id FK
        varchar owner_id FK
        varchar alert_id null
        text message "🚨 Alerta: Exceso de velocidad detectado"
        enum channel "sms|email|push|emergency_call"
        enum status "pending|sent|delivered|failed"
        varchar recipient "+573001234567|juan@correo.com"
        jsonb metadata "{\"provider\":\"twilio\",\"cost\":0.05}"
        timestamp sent_at "2024-01-15 10:30:10"
        timestamp delivered_at "2024-01-15 10:30:15"
        int retry_count 0
    }
    
    VEHICLE_GROUPS {
        serial id PK
        varchar name "Flota_Norte"
        varchar description "Vehículos operando en zona norte"
        varchar owner_id FK
        jsonb vehicle_ids "[\"TRUCK-001\",\"TRUCK-002\",\"CAR-101\"]"
        timestamp created_at "2024-01-01"
        boolean active true
    }
    
    API_LOGS {
        bigserial id PK
        varchar endpoint "/signal|/rules|/health"
        varchar method "POST|GET|PUT"
        int status_code 200|202|400|500
        varchar vehicle_id null
        real processing_time_ms 45.2
        jsonb request_headers "{\"user-agent\":\"CCS-Sensor/1.0\"}"
        jsonb response_data null
        timestamp timestamp "2024-01-15 10:30:00"
        varchar api_instance "ccs-api-a1b2c3d4"
    }
```

## Esquema SQL Optimizado

### 1. Tabla `owners` - Dueños de vehículos
```sql
CREATE TABLE owners (
    id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    emergency_contact VARCHAR(20),
    notifications_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT owners_email_unique UNIQUE (email),
    CONSTRAINT owners_phone_unique UNIQUE (phone)
);

CREATE INDEX idx_owners_created ON owners(created_at);
```

### 2. Tabla `vehicles` - Vehículos monitoreados
```sql
CREATE TABLE vehicles (
    id VARCHAR(20) PRIMARY KEY,
    owner_id VARCHAR(50) NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
    type VARCHAR(10) NOT NULL CHECK (type IN ('TRUCK', 'CAR', 'MOTO')),
    license_plate VARCHAR(15),
    manufacturer VARCHAR(50),
    model VARCHAR(50),
    manufacturing_year INT CHECK (manufacturing_year >= 1900 AND manufacturing_year <= EXTRACT(YEAR FROM CURRENT_DATE) + 1),
    active BOOLEAN DEFAULT TRUE,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_signal_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT vehicles_license_plate_unique UNIQUE (license_plate)
);

-- Índices críticos
CREATE INDEX idx_vehicles_owner ON vehicles(owner_id);
CREATE INDEX idx_vehicles_type_active ON vehicles(type) WHERE active = TRUE;
CREATE INDEX idx_vehicles_last_signal ON vehicles(last_signal_at DESC) WHERE active = TRUE;
```

### 3. Tabla `rules` - Reglas de negocio configurables
```sql
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    rule_type VARCHAR(30) NOT NULL CHECK (rule_type IN (
        'MAX_SPEED', 'PANIC_BUTTON', 'MAX_TEMP', 'MIN_TEMP', 
        'GEOFENCE_EXIT', 'SCHEDULE', 'UNPLANNED_STOP', 'DOOR_SENSOR'
    )),
    comparison_value TEXT NOT NULL,
    action_type VARCHAR(30) NOT NULL CHECK (action_type IN (
        'NOTIFY_POLICE', 'NOTIFY_OWNER', 'SMS_OWNER', 
        'LOG_ONLY', 'CALL_EMERGENCY', 'NOTIFY_SECURITY'
    )),
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 1 CHECK (priority BETWEEN 1 AND 10),
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_vehicle_rule_type UNIQUE (vehicle_id, rule_type) 
    WHERE is_active = TRUE
);

-- Índices para consultas frecuentes
CREATE INDEX idx_rules_vehicle_active ON rules(vehicle_id) WHERE is_active = TRUE;
CREATE INDEX idx_rules_type_active ON rules(rule_type) WHERE is_active = TRUE;
CREATE INDEX idx_rules_priority ON rules(priority DESC) WHERE is_active = TRUE;
```

### 4. Tabla `signals` - Señales recibidas (PARTICIONADA)
```sql
-- Tabla principal particionada
CREATE TABLE signals (
    id BIGSERIAL,
    vehicle_id VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    speed REAL DEFAULT 0.0 CHECK (speed >= 0),
    heading REAL DEFAULT 0.0 CHECK (heading >= 0 AND heading < 360),
    temperature REAL,
    panic_button BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    api_instance VARCHAR(50),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Partición para el mes actual
CREATE TABLE signals_2024_01 PARTITION OF signals
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Partición para el próximo mes
CREATE TABLE signals_2024_02 PARTITION OF signals
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Partición por defecto
CREATE TABLE signals_default PARTITION OF signals DEFAULT;

-- Índices por partición (automáticamente aplicados a todas las particiones)
CREATE INDEX idx_signals_vehicle_time ON signals(vehicle_id, timestamp DESC);
CREATE INDEX idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX idx_signals_panic_button ON signals(panic_button) WHERE panic_button = TRUE;
CREATE INDEX idx_signals_location ON signals USING GIST (
    ST_MakePoint(longitude, latitude)
);

-- Índice BRIN para rangos temporales (muy eficiente en espacio)
CREATE INDEX idx_signals_brin_time ON signals USING BRIN (timestamp);
```

### 5. Tabla `alerts` - Alertas generadas
```sql
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL REFERENCES vehicles(id),
    rule_id INT REFERENCES rules(id),
    signal_id BIGINT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message TEXT NOT NULL,
    action_taken TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'generated' CHECK (status IN ('generated', 'notified', 'resolved')),
    details JSONB DEFAULT '{}'::jsonb,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT fk_signal FOREIGN KEY (signal_id) REFERENCES signals(id)
);

-- Índices para reportes y consultas
CREATE INDEX idx_alerts_vehicle_time ON alerts(vehicle_id, timestamp DESC);
CREATE INDEX idx_alerts_signal ON alerts(signal_id);
CREATE INDEX idx_alerts_rule ON alerts(rule_id);
CREATE INDEX idx_alerts_status ON alerts(status) WHERE status != 'resolved';
CREATE INDEX idx_alerts_resolved ON alerts(resolved_at) WHERE resolved_at IS NOT NULL;
```

### 6. Tabla `geofences` - Geocercas definidas
```sql
CREATE TABLE geofences (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    description TEXT,
    center JSONB NOT NULL CHECK (
        center ? 'latitude' AND center ? 'longitude' AND
        (center->>'latitude')::numeric BETWEEN -90 AND 90 AND
        (center->>'longitude')::numeric BETWEEN -180 AND 180
    ),
    radius_km DOUBLE PRECISION NOT NULL CHECK (radius_km > 0),
    is_allowed BOOLEAN DEFAULT TRUE,
    polygon_coordinates JSONB, -- Para polígonos complejos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    active_until TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT unique_vehicle_geofence_name UNIQUE (vehicle_id, name)
);

-- Índice para búsquedas espaciales
CREATE INDEX idx_geofences_vehicle ON geofences(vehicle_id);
CREATE INDEX idx_geofences_active ON geofences(active_until) WHERE active_until > CURRENT_TIMESTAMP;
```

### 7. Tabla `schedules` - Horarios programados
```sql
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week INT[] NOT NULL CHECK (
        array_length(days_of_week, 1) BETWEEN 1 AND 7 AND
        array_position(days_of_week, 0) IS NULL AND
        array_position(days_of_week, 8) IS NULL
    ),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_valid_time_range CHECK (start_time < end_time),
    CONSTRAINT unique_vehicle_schedule_name UNIQUE (vehicle_id, name)
);

-- Índices para consultas frecuentes
CREATE INDEX idx_schedules_vehicle ON schedules(vehicle_id) WHERE active = TRUE;
CREATE INDEX idx_schedules_days ON schedules USING GIN (days_of_week);
```

### 8. Tabla `notifications` - Histórico de notificaciones
```sql
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL REFERENCES vehicles(id),
    owner_id VARCHAR(50) NOT NULL REFERENCES owners(id),
    alert_id BIGINT REFERENCES alerts(id),
    message TEXT NOT NULL,
    channel VARCHAR(20) NOT NULL CHECK (channel IN ('sms', 'email', 'push', 'emergency_call')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'sent', 'delivered', 'failed')),
    recipient VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    retry_count INT DEFAULT 0 CHECK (retry_count >= 0),
    
    CONSTRAINT check_notification_timestamps CHECK (
        (sent_at IS NULL OR delivered_at IS NULL OR sent_at <= delivered_at)
    )
);

-- Índices para seguimiento y reportes
CREATE INDEX idx_notifications_vehicle ON notifications(vehicle_id);
CREATE INDEX idx_notifications_owner ON notifications(owner_id);
CREATE INDEX idx_notifications_status ON notifications(status);
CREATE INDEX idx_notifications_sent_date ON notifications(date(sent_at));
CREATE INDEX idx_notifications_channel ON notifications(channel);
```

## Estrategias de Optimización

### 1. Particionamiento por Tiempo
```sql
-- Función para crear particiones automáticamente
CREATE OR REPLACE FUNCTION create_signal_partition_if_not_exists(
    partition_date DATE
) RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date DATE;
    end_date DATE;
BEGIN
    partition_name := 'signals_' || TO_CHAR(partition_date, 'YYYY_MM');
    start_date := DATE_TRUNC('month', partition_date);
    end_date := start_date + INTERVAL '1 month';
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_tables 
        WHERE tablename = partition_name
    ) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF signals FOR VALUES FROM (%L) TO (%L)',
            partition_name, start_date, end_date
        );
        
        RAISE NOTICE 'Partición creada: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Job mensual para crear partición futura
SELECT create_signal_partition_if_not_exists(
    CURRENT_DATE + INTERVAL '1 month'
);
```

### 2. Índices Parciales para Performance
```sql
-- Solo señales recientes (últimos 30 días)
CREATE INDEX idx_signals_recent ON signals(timestamp DESC, vehicle_id) 
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '30 days';

-- Solo alertas no resueltas
CREATE INDEX idx_alerts_pending ON alerts(timestamp DESC) 
WHERE status != 'resolved';

-- Solo vehículos activos con reglas
CREATE INDEX idx_vehicles_active_rules ON vehicles(id) 
WHERE active = TRUE AND EXISTS (
    SELECT 1 FROM rules 
    WHERE rules.vehicle_id = vehicles.id 
    AND rules.is_active = TRUE
);
```

### 3. Vistas Materializadas para Reportes
```sql
-- Vista para dashboard en tiempo real
CREATE MATERIALIZED VIEW mv_daily_metrics AS
SELECT 
    DATE(timestamp) as date,
    vehicle_id,
    COUNT(*) as signals_count,
    COUNT(CASE WHEN panic_button THEN 1 END) as emergencies_count,
    AVG(speed) as avg_speed,
    MIN(speed) as min_speed,
    MAX(speed) as max_speed
FROM signals
WHERE timestamp > CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(timestamp), vehicle_id
WITH DATA;

-- Actualizar cada 5 minutos
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_metrics;
```

### 4. Tabla de Agregados para Métricas
```sql
CREATE TABLE signal_aggregates_hourly (
    hour TIMESTAMP WITH TIME ZONE PRIMARY KEY,
    total_signals BIGINT DEFAULT 0,
    total_emergencies BIGINT DEFAULT 0,
    avg_processing_time_ms REAL,
    p95_processing_time_ms REAL,
    vehicle_count INT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índice para consultas rápidas
CREATE INDEX idx_aggregates_hour ON signal_aggregates_hourly(hour DESC);
```

## Cálculos de Escalabilidad

### Crecimiento Proyectado (20% anual)
```sql
-- Cálculo de crecimiento de datos
WITH current_stats AS (
    SELECT 
        COUNT(*) as current_vehicles,
        COUNT(DISTINCT DATE(timestamp)) as avg_signals_per_day
    FROM signals
    WHERE timestamp > CURRENT_DATE - INTERVAL '30 days'
),
projection AS (
    SELECT 
        current_vehicles,
        current_vehicles * 1.2 as year_1,
        current_vehicles * 1.44 as year_2,
        current_vehicles * 1.728 as year_3,
        avg_signals_per_day,
        avg_signals_per_day * 500 as estimated_daily_signals -- 500 RPS × segundos/día
    FROM current_stats
)
SELECT * FROM projection;
```

### Estimación de Espacio de Almacenamiento
```sql
-- Tamaño estimado por tabla
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(quote_ident(tablename))) as total_size,
    pg_size_pretty(pg_relation_size(quote_ident(tablename))) as table_size,
    pg_size_pretty(pg_total_relation_size(quote_ident(tablename)) - 
                   pg_relation_size(quote_ident(tablename))) as index_size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(quote_ident(tablename)) DESC;
```

## Consultas Optimizadas para el Sistema

### 1. Obtener Reglas Activas por Vehículo (Cache Warmup)
```sql
-- Usada por DataService.get_rules()
SELECT id, rule_type, comparison_value, action_type, priority 
FROM rules 
WHERE vehicle_id = $1 
  AND is_active = TRUE 
ORDER BY priority DESC;
-- Índice: idx_rules_vehicle_active
```

### 2. Obtener Últimas Señales para Detección de Paradas
```sql
-- Usada por RuleService._check_unplanned_stop()
SELECT speed, timestamp 
FROM signals 
WHERE vehicle_id = $1 
  AND timestamp > NOW() - INTERVAL '5 minutes'
ORDER BY timestamp DESC 
LIMIT 10;
-- Índice: idx_signals_vehicle_time
```

### 3. Reporte de Alertas por Período
```sql
-- Para dashboard administrativo
SELECT 
    a.vehicle_id,
    v.type as vehicle_type,
    r.rule_type,
    COUNT(*) as alert_count,
    MIN(a.timestamp) as first_alert,
    MAX(a.timestamp) as last_alert
FROM alerts a
JOIN vehicles v ON a.vehicle_id = v.id
LEFT JOIN rules r ON a.rule_id = r.id
WHERE a.timestamp BETWEEN $1 AND $2
  AND a.status != 'resolved'
GROUP BY a.vehicle_id, v.type, r.rule_type
ORDER BY alert_count DESC;
```

### 4. Consulta Espacial para Geocercas
```sql
-- Verificar si vehículo está dentro de geocerca
SELECT EXISTS (
    SELECT 1 FROM geofences g
    WHERE g.vehicle_id = $1
      AND g.active_until > CURRENT_TIMESTAMP
      AND ST_Distance_Sphere(
          ST_MakePoint($2, $3),  -- posición actual
          ST_MakePoint(
              (g.center->>'longitude')::numeric,
              (g.center->>'latitude')::numeric
          )
      ) <= g.radius_km * 1000  -- convertir km a metros
) as is_within_geofence;
```

## Estrategias de Mantenimiento

### 1. Rotación de Particiones Antiguas
```sql
-- Archivar particiones mayores a 13 meses
CREATE OR REPLACE PROCEDURE archive_old_partitions() AS $$
DECLARE
    old_partition RECORD;
BEGIN
    FOR old_partition IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE tablename LIKE 'signals_%' 
          AND tablename < 'signals_' || TO_CHAR(CURRENT_DATE - INTERVAL '13 months', 'YYYY_MM')
    LOOP
        -- Crear tabla de archivo
        EXECUTE format(
            'CREATE TABLE %I_archive (LIKE %I INCLUDING ALL)',
            old_partition.tablename, old_partition.tablename
        );
        
        -- Copiar datos
        EXECUTE format(
            'INSERT INTO %I_archive SELECT * FROM %I',
            old_partition.tablename, old_partition.tablename
        );
        
        -- Eliminar partición (los datos quedan en tabla de archivo)
        EXECUTE format(
            'DROP TABLE %I',
            old_partition.tablename
        );
        
        RAISE NOTICE 'Partición archivada: %', old_partition.tablename;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

### 2. Limpieza de Datos Temporales
```sql
-- Eliminar señales muy antiguas (política de retención)
DELETE FROM signals 
WHERE timestamp < CURRENT_DATE - INTERVAL '3 years'
  AND panic_button = FALSE;

-- Marcar alertas antiguas como resueltas
UPDATE alerts 
SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
WHERE timestamp < CURRENT_DATE - INTERVAL '90 days'
  AND status = 'generated';
```

### 3. Vacuum y Analyze Programado
```sql
-- Optimizar tablas particionadas
VACUUM (ANALYZE, VERBOSE) signals;

-- Actualizar estadísticas
ANALYZE signals;
ANALYZE alerts;
ANALYZE rules;
```

## Consideraciones de Seguridad

### 1. Roles y Permisos
```sql
-- Crear roles específicos
CREATE ROLE ccs_api LOGIN PASSWORD 'secure_password';
CREATE ROLE ccs_readonly LOGIN PASSWORD 'readonly_password';

-- Permisos para API
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA public TO ccs_api;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ccs_api;

-- Permisos de solo lectura para reportes
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ccs_readonly;
```

### 2. Encriptación de Datos Sensibles
```sql
-- Usar pgcrypto para datos sensibles
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encriptar número de teléfono
UPDATE owners 
SET phone_encrypted = pgp_sym_encrypt(phone, 'encryption_key')
WHERE phone IS NOT NULL;
```

## Métricas de Performance Esperadas

### Consultas Clave
| Consulta | Tabla | Tiempo Esperado | Índice Usado |
|----------|-------|-----------------|--------------|
| Obtener reglas activas | rules | < 10ms | idx_rules_vehicle_active |
| Insertar señal | signals | < 50ms | Partición actual |
| Últimas 10 señales | signals | < 20ms | idx_signals_vehicle_time |
| Alertas no resueltas | alerts | < 30ms | idx_alerts_status |
| Verificación geocerca | geofences | < 15ms | idx_geofences_vehicle |

### Capacidad de Almacenamiento
| Tabla | Tamaño Estimado (Año 1) | Crecimiento Anual |
|-------|-------------------------|-------------------|
| signals | 500 GB | 120 GB/mes |
| alerts | 50 GB | 12 GB/mes |
| rules | 5 MB | 1 MB/mes |
| geofences | 10 MB | 2 MB/mes |
| notifications | 100 GB | 24 GB/mes |

---

**Archivo:** `docs/architecture/04_entity_relationship.md`  
**Versión:** 1.0  
**Última actualización:** Enero 2024  
**Responsable:** Equipo de Arquitectura CCS