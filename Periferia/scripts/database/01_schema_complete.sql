/*
 * CCS - CENTRAL DE SEGUIMIENTO VEHICULAR
 * SCRIPT: Esquema Estructural (DDL)
 * VERSIÓN: 2.0 (Corregida con signal_id)
 */

-- =================================================================================
-- 1. LIMPIEZA DE ENTORNO (Borra todo para iniciar limpio)
-- =================================================================================
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS rules CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS owners CASCADE;

-- =================================================================================
-- 2. CREACIÓN DE TABLAS (ESQUEMA)
-- =================================================================================

-- 2.1 DUEÑOS
CREATE TABLE owners (
    id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2.2 VEHÍCULOS
CREATE TABLE vehicles (
    id VARCHAR(20) PRIMARY KEY,
    owner_id VARCHAR(50) NOT NULL REFERENCES owners(id),
    type VARCHAR(20) NOT NULL CHECK (type IN ('TRUCK', 'CAR', 'MOTO')),
    active BOOLEAN DEFAULT TRUE,
    details JSONB DEFAULT '{}'::jsonb, -- Flexibilidad para metadatos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vehicles_owner ON vehicles(owner_id);

-- 2.3 REGLAS (Configuración)
CREATE TABLE rules (
    id SERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL REFERENCES vehicles(id),
    rule_type VARCHAR(50) NOT NULL, 
    comparison_value TEXT NOT NULL, 
    action_type VARCHAR(50) NOT NULL, 
    is_active BOOLEAN DEFAULT TRUE,
    priority INT DEFAULT 1
);

-- Índice crítico para Cache Warmer (Carga rápida en Redis)
CREATE INDEX idx_rules_vehicle_active ON rules(vehicle_id) WHERE is_active = TRUE;

-- 2.4 SEÑALES (Tabla Particionada - El corazón del rendimiento)
CREATE TABLE signals (
    id BIGSERIAL, 
    vehicle_id VARCHAR(20) NOT NULL, 
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    speed REAL DEFAULT 0.0,
    heading REAL DEFAULT 0.0,
    metadata JSONB DEFAULT '{}'::jsonb, 
    PRIMARY KEY (id, timestamp) 
) PARTITION BY RANGE (timestamp);

-- 2.5 ALERTAS (Histórico) -- [CORREGIDO AQUÍ]
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL,
    rule_id INT,
    
    -- NUEVA COLUMNA NECESARIA PARA EL SEED DATA
    signal_id BIGINT, 
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message TEXT NOT NULL, 
    action_taken TEXT NOT NULL
);

-- Índices para reportes
CREATE INDEX idx_alerts_vehicle_time ON alerts(vehicle_id, timestamp DESC);
-- Nuevo índice para buscar rápido qué alerta generó una señal específica
CREATE INDEX idx_alerts_signal ON alerts(signal_id);

-- =================================================================================
-- 3. GESTIÓN DE PARTICIONES E ÍNDICES (LA ESTRATEGIA OPTIMIZADA)
-- =================================================================================

-- A. Crear las particiones para los próximos meses
CREATE TABLE signals_2026_01 PARTITION OF signals FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE signals_2026_02 PARTITION OF signals FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
CREATE TABLE signals_def PARTITION OF signals DEFAULT;

-- B. Crear el índice en la tabla PADRE.
-- PostgreSQL aplicará esto automáticamente a las particiones hijas.
CREATE INDEX idx_signals_vehicle_time ON signals(vehicle_id, timestamp DESC);