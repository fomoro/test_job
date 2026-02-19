/*
 * CCS - CENTRAL DE SEGUIMIENTO VEHICULAR
 * SCRIPT: 02_seed_master_data.sql
 * DESCRIPCIÓN: Carga de datos maestros (Dueños, Vehículos, Reglas)
 * CANTIDAD: ~20 Owners, ~70 Vehicles, ~90 Rules
 */

-- =================================================================================
-- 1. LIMPIEZA PREVENTIVA (Para evitar duplicados si se corre varias veces)
-- =================================================================================
TRUNCATE TABLE rules, vehicles, owners RESTART IDENTITY CASCADE;

-- =================================================================================
-- 2. DUEÑOS (OWNERS) - 20 Registros
-- =================================================================================
INSERT INTO owners (id, full_name, email, phone) VALUES 
    -- Empresas Grandes
    ('1001', 'Logística Nacional S.A.', 'flota@logistica-nal.com', '+576015550001'),
    ('1002', 'Transportes El Rápido', 'contacto@elrapido.co', '+576015550002'),
    ('1003', 'Carga Fría Ltda', 'ops@cargafria.com', '+576015550003'),
    ('1004', 'Constructora Metro', 'maquinaria@metro.com', '+576015550004'),
    ('1005', 'Distribuidora de Bebidas', 'logistica@bebidas.com', '+576015550005'),
    
    -- Flotas de Transporte
    ('1006', 'Taxis Libres Bogotá', 'admin@taxislibres.com.co', '+576015550006'),
    ('1007', 'Uber Fleet Partners', 'partners@uberfleet.com', '+573005550007'),
    ('1008', 'Transmilenio Alimentadores', 'control@sitp.gov.co', '+576015550008'),
    
    -- Apps de Domicilios
    ('1009', 'Rappi Aliados Norte', 'soporte@rappi.com', '+573005550009'),
    ('1010', 'Mensajeros Urbanos', 'ops@mensajeros.com', '+573005550010'),
    ('1011', 'Didi Moto Flota', 'drivers@didi.com', '+573005550011'),

    -- Particulares (Dueños individuales y VIPs)
    ('1012', 'Juan Pablo Montoya', 'jpm@speed.com', '+573101234567'),
    ('1013', 'Sofía Vergara', 'sofia@hollywood.com', '+573107654321'),
    ('1014', 'James Rodriguez', 'james@futbol.com', '+573101112222'),
    ('1015', 'Shakira Mebarak', 'shaki@music.com', '+573103334444'),
    ('1016', 'Radamel Falcao', 'tigre@gol.com', '+573105556666'),
    ('1017', 'Egan Bernal', 'egan@ineos.com', '+573107778888'),
    ('1018', 'Nairo Quintana', 'nairo@movistar.com', '+573109990000'),
    ('1019', 'Mariana Pajon', 'mariana@bmx.com', '+573101231234'),
    ('1020', 'Rigoberto Uran', 'rigo@gorigogo.com', '+573109879876');

-- =================================================================================
-- 3. VEHÍCULOS (VEHICLES) - 70 Registros
-- =================================================================================
INSERT INTO vehicles (id, owner_id, type, details) VALUES 
    -- === FLOTA 1: CAMIONES PESADOS (20 Vehículos) ===
    ('TRUCK-001', '1001', 'TRUCK', '{"capacity": "30ton", "brand": "Kenworth", "gps_model": "X1"}'),
    ('TRUCK-002', '1001', 'TRUCK', '{"capacity": "30ton", "brand": "Kenworth", "gps_model": "X1"}'),
    ('TRUCK-003', '1001', 'TRUCK', '{"capacity": "30ton", "brand": "Kenworth", "gps_model": "X1"}'),
    ('TRUCK-004', '1001', 'TRUCK', '{"capacity": "20ton", "brand": "International", "gps_model": "X2"}'),
    ('TRUCK-005', '1001', 'TRUCK', '{"capacity": "20ton", "brand": "International", "gps_model": "X2"}'),
    ('TRUCK-006', '1002', 'TRUCK', '{"capacity": "10ton", "brand": "Hino", "service": "express"}'),
    ('TRUCK-007', '1002', 'TRUCK', '{"capacity": "10ton", "brand": "Hino", "service": "express"}'),
    ('TRUCK-008', '1002', 'TRUCK', '{"capacity": "10ton", "brand": "Hino", "service": "express"}'),
    ('TRUCK-009', '1002', 'TRUCK', '{"capacity": "5ton", "brand": "Foton", "service": "urban"}'),
    ('TRUCK-010', '1002', 'TRUCK', '{"capacity": "5ton", "brand": "Foton", "service": "urban"}'),
    ('TRUCK-011', '1003', 'TRUCK', '{"type": "reefer", "temp_min": -20, "brand": "ThermoKing"}'),
    ('TRUCK-012', '1003', 'TRUCK', '{"type": "reefer", "temp_min": -20, "brand": "ThermoKing"}'),
    ('TRUCK-013', '1003', 'TRUCK', '{"type": "reefer", "temp_min": -5, "brand": "ThermoKing"}'),
    ('TRUCK-014', '1003', 'TRUCK', '{"type": "reefer", "temp_min": -5, "brand": "ThermoKing"}'),
    ('TRUCK-015', '1004', 'TRUCK', '{"type": "mixer", "capacity": "8m3", "brand": "Mack"}'),
    ('TRUCK-016', '1004', 'TRUCK', '{"type": "mixer", "capacity": "8m3", "brand": "Mack"}'),
    ('TRUCK-017', '1004', 'TRUCK', '{"type": "dump", "capacity": "12m3", "brand": "Caterpillar"}'),
    ('TRUCK-018', '1004', 'TRUCK', '{"type": "dump", "capacity": "12m3", "brand": "Caterpillar"}'),
    ('TRUCK-019', '1005', 'TRUCK', '{"type": "distribution", "zone": "North", "brand": "Chevrolet"}'),
    ('TRUCK-020', '1005', 'TRUCK', '{"type": "distribution", "zone": "South", "brand": "Chevrolet"}'),

    -- === FLOTA 2: TAXIS Y UBER (20 Vehículos) ===
    ('TAXI-101', '1006', 'CAR', '{"color": "yellow", "brand": "Kia", "model": "Picanto"}'),
    ('TAXI-102', '1006', 'CAR', '{"color": "yellow", "brand": "Kia", "model": "Picanto"}'),
    ('TAXI-103', '1006', 'CAR', '{"color": "yellow", "brand": "Hyundai", "model": "i10"}'),
    ('TAXI-104', '1006', 'CAR', '{"color": "yellow", "brand": "Hyundai", "model": "i10"}'),
    ('TAXI-105', '1006', 'CAR', '{"color": "yellow", "brand": "Hyundai", "model": "Atos"}'),
    ('TAXI-106', '1006', 'CAR', '{"color": "yellow", "brand": "Hyundai", "model": "Accent"}'),
    ('TAXI-107', '1006', 'CAR', '{"color": "yellow", "brand": "Renault", "model": "Logan"}'),
    ('TAXI-108', '1006', 'CAR', '{"color": "yellow", "brand": "Renault", "model": "Logan"}'),
    ('TAXI-109', '1006', 'CAR', '{"color": "yellow", "brand": "Chevrolet", "model": "Spark"}'),
    ('TAXI-110', '1006', 'CAR', '{"color": "yellow", "brand": "Chevrolet", "model": "Spark"}'),
    ('UBER-201', '1007', 'CAR', '{"color": "black", "brand": "Renault", "model": "Duster"}'),
    ('UBER-202', '1007', 'CAR', '{"color": "silver", "brand": "Renault", "model": "Kwid"}'),
    ('UBER-203', '1007', 'CAR', '{"color": "white", "brand": "Chevrolet", "model": "Onix"}'),
    ('UBER-204', '1007', 'CAR', '{"color": "gray", "brand": "Mazda", "model": "2"}'),
    ('UBER-205', '1007', 'CAR', '{"color": "blue", "brand": "Nissan", "model": "Versa"}'),
    ('UBER-206', '1007', 'CAR', '{"color": "red", "brand": "Nissan", "model": "March"}'),
    ('UBER-207', '1007', 'CAR', '{"color": "white", "brand": "Toyota", "model": "Corolla"}'),
    ('UBER-208', '1007', 'CAR', '{"color": "black", "brand": "Toyota", "model": "Yaris"}'),
    ('UBER-209', '1007', 'CAR', '{"color": "silver", "brand": "Ford", "model": "Fiesta"}'),
    ('UBER-210', '1007', 'CAR', '{"color": "gray", "brand": "Volkswagen", "model": "Gol"}'),

    -- === FLOTA 3: MOTOS DOMICILIOS (20 Vehículos) ===
    ('MOTO-301', '1009', 'MOTO', '{"cc": 125, "brand": "Honda", "box": "Rappi"}'),
    ('MOTO-302', '1009', 'MOTO', '{"cc": 125, "brand": "Honda", "box": "Rappi"}'),
    ('MOTO-303', '1009', 'MOTO', '{"cc": 150, "brand": "Bajaj", "box": "Rappi"}'),
    ('MOTO-304', '1009', 'MOTO', '{"cc": 150, "brand": "Bajaj", "box": "Rappi"}'),
    ('MOTO-305', '1009', 'MOTO', '{"cc": 100, "brand": "TVS", "box": "Rappi"}'),
    ('MOTO-306', '1010', 'MOTO', '{"cc": 150, "brand": "Yamaha", "box": "Mensajeros"}'),
    ('MOTO-307', '1010', 'MOTO', '{"cc": 150, "brand": "Yamaha", "box": "Mensajeros"}'),
    ('MOTO-308', '1010', 'MOTO', '{"cc": 125, "brand": "Suzuki", "box": "Mensajeros"}'),
    ('MOTO-309', '1010', 'MOTO', '{"cc": 125, "brand": "Suzuki", "box": "Mensajeros"}'),
    ('MOTO-310', '1010', 'MOTO', '{"cc": 200, "brand": "KTM", "box": "Mensajeros"}'),
    ('MOTO-311', '1011', 'MOTO', '{"cc": 125, "brand": "AKT", "type": "delivery"}'),
    ('MOTO-312', '1011', 'MOTO', '{"cc": 125, "brand": "AKT", "type": "delivery"}'),
    ('MOTO-313', '1011', 'MOTO', '{"cc": 125, "brand": "AKT", "type": "delivery"}'),
    ('MOTO-314', '1011', 'MOTO', '{"cc": 150, "brand": "Hero", "type": "delivery"}'),
    ('MOTO-315', '1011', 'MOTO', '{"cc": 150, "brand": "Hero", "type": "delivery"}'),
    ('MOTO-316', '1011', 'MOTO', '{"cc": 100, "brand": "Bajaj", "type": "delivery"}'),
    ('MOTO-317', '1011', 'MOTO', '{"cc": 100, "brand": "Bajaj", "type": "delivery"}'),
    ('MOTO-318', '1011', 'MOTO', '{"cc": 150, "brand": "Yamaha", "type": "delivery"}'),
    ('MOTO-319', '1011', 'MOTO', '{"cc": 150, "brand": "Yamaha", "type": "delivery"}'),
    ('MOTO-320', '1011', 'MOTO', '{"cc": 250, "brand": "Honda", "type": "delivery"}'),

    -- === FLOTA 4: PARTICULARES VIP (10 Vehículos) ===
    ('FERRARI-01', '1012', 'CAR', '{"color": "red", "brand": "Ferrari", "model": "F8"}'),
    ('PORSCHE-01', '1013', 'CAR', '{"color": "black", "brand": "Porsche", "model": "Cayenne"}'),
    ('BMW-01', '1014', 'CAR', '{"color": "blue", "brand": "BMW", "model": "M3"}'),
    ('MERCEDES-01', '1015', 'CAR', '{"color": "white", "brand": "Mercedes", "model": "GLE"}'),
    ('AUDI-01', '1016', 'CAR', '{"color": "gray", "brand": "Audi", "model": "Q8"}'),
    ('PINARELLO-01', '1017', 'MOTO', '{"type": "scooter_vip", "brand": "Vespa"}'),
    ('CANYON-01', '1018', 'CAR', '{"color": "blue", "brand": "Volvo", "model": "XC90"}'),
    ('BMX-01', '1019', 'CAR', '{"color": "gold", "brand": "Land Rover", "model": "Defender"}'),
    ('CANNON-01', '1020', 'MOTO', '{"type": "touring", "brand": "Ducati", "cc": 1200}'),
    ('TESLA-01', '1012', 'CAR', '{"color": "white", "brand": "Tesla", "model": "Model X"}');

-- =================================================================================
-- 4. REGLAS DE NEGOCIO (RULES) - +90 Reglas
-- =================================================================================
INSERT INTO rules (vehicle_id, rule_type, comparison_value, action_type, priority) VALUES 
    -- REGLAS CAMIONES (Todos velocidad + algunos temperatura)
    ('TRUCK-001', 'MAX_SPEED', '80.0', 'NOTIFY_POLICE', 1), ('TRUCK-001', 'DOOR_SENSOR', 'OPEN', 'NOTIFY_OWNER', 2),
    ('TRUCK-002', 'MAX_SPEED', '80.0', 'NOTIFY_POLICE', 1),
    ('TRUCK-003', 'MAX_SPEED', '80.0', 'NOTIFY_POLICE', 1),
    ('TRUCK-004', 'MAX_SPEED', '80.0', 'NOTIFY_POLICE', 1),
    ('TRUCK-005', 'MAX_SPEED', '80.0', 'NOTIFY_POLICE', 1),
    ('TRUCK-006', 'MAX_SPEED', '75.0', 'LOG_ONLY', 1),
    ('TRUCK-007', 'MAX_SPEED', '75.0', 'LOG_ONLY', 1),
    ('TRUCK-008', 'MAX_SPEED', '75.0', 'LOG_ONLY', 1),
    ('TRUCK-009', 'MAX_SPEED', '60.0', 'NOTIFY_OWNER', 1), -- Urbano lento
    ('TRUCK-010', 'MAX_SPEED', '60.0', 'NOTIFY_OWNER', 1),
    -- Refrigerados (Regla doble)
    ('TRUCK-011', 'TEMP_MAX', '-18.0', 'NOTIFY_OWNER', 5), ('TRUCK-011', 'MAX_SPEED', '80.0', 'LOG_ONLY', 1),
    ('TRUCK-012', 'TEMP_MAX', '-18.0', 'NOTIFY_OWNER', 5), ('TRUCK-012', 'MAX_SPEED', '80.0', 'LOG_ONLY', 1),
    ('TRUCK-013', 'TEMP_MAX', '-4.0', 'NOTIFY_OWNER', 5),
    ('TRUCK-014', 'TEMP_MAX', '-4.0', 'NOTIFY_OWNER', 5),
    -- Obra (Geocercas)
    ('TRUCK-015', 'GEOFENCE_EXIT', 'ZONE_OBRA_1', 'NOTIFY_POLICE', 2),
    ('TRUCK-016', 'GEOFENCE_EXIT', 'ZONE_OBRA_1', 'NOTIFY_POLICE', 2),
    ('TRUCK-017', 'GEOFENCE_EXIT', 'ZONE_OBRA_2', 'NOTIFY_POLICE', 2),
    ('TRUCK-018', 'GEOFENCE_EXIT', 'ZONE_OBRA_2', 'NOTIFY_POLICE', 2),
    ('TRUCK-019', 'MAX_SPEED', '70.0', 'LOG_ONLY', 1),
    ('TRUCK-020', 'MAX_SPEED', '70.0', 'LOG_ONLY', 1),

    -- REGLAS TAXIS (Botón pánico + Velocidad)
    ('TAXI-101', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10), ('TAXI-101', 'MAX_SPEED', '60.0', 'LOG_ONLY', 1),
    ('TAXI-102', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('TAXI-103', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('TAXI-104', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('TAXI-105', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('TAXI-106', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('TAXI-107', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('TAXI-108', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('TAXI-109', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('TAXI-110', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),

    -- REGLAS UBER (Similar a taxis pero sin pánico automático)
    ('UBER-201', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-202', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-203', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-204', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-205', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-206', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-207', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-208', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-209', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),
    ('UBER-210', 'MAX_SPEED', '100.0', 'SMS_OWNER', 1),

    -- REGLAS MOTOS (Horarios y Zonas)
    ('MOTO-301', 'SCHEDULE', '22:00-05:00', 'NOTIFY_OWNER', 2),
    ('MOTO-302', 'SCHEDULE', '22:00-05:00', 'NOTIFY_OWNER', 2),
    ('MOTO-303', 'SCHEDULE', '22:00-05:00', 'NOTIFY_OWNER', 2),
    ('MOTO-304', 'SCHEDULE', '22:00-05:00', 'NOTIFY_OWNER', 2),
    ('MOTO-305', 'SCHEDULE', '22:00-05:00', 'NOTIFY_OWNER', 2),
    ('MOTO-306', 'GEOFENCE_EXIT', 'ZONE_NORTE', 'LOG_ONLY', 1),
    ('MOTO-307', 'GEOFENCE_EXIT', 'ZONE_NORTE', 'LOG_ONLY', 1),
    ('MOTO-308', 'GEOFENCE_EXIT', 'ZONE_SUR', 'LOG_ONLY', 1),
    ('MOTO-309', 'GEOFENCE_EXIT', 'ZONE_SUR', 'LOG_ONLY', 1),
    ('MOTO-310', 'MAX_SPEED', '80.0', 'NOTIFY_OWNER', 1),
    
    -- REGLAS VIP (Reglas más estrictas o especiales)
    ('FERRARI-01', 'MAX_SPEED', '200.0', 'SMS_OWNER', 1), -- Le permiten correr más
    ('FERRARI-01', 'PANIC_BUTTON', 'TRUE', 'NOTIFY_POLICE', 10),
    ('PORSCHE-01', 'MAX_SPEED', '180.0', 'SMS_OWNER', 1),
    ('BMW-01', 'MAX_SPEED', '150.0', 'SMS_OWNER', 1),
    ('MERCEDES-01', 'GEOFENCE_EXIT', 'COUNTRY_CLUB', 'SMS_OWNER', 2),
    ('CANNON-01', 'MAX_SPEED', '250.0', 'NOTIFY_POLICE', 5);

-- =================================================================================
-- 5. VERIFICACIÓN FINAL
-- =================================================================================
SELECT 'Owners' as tabla, count(*) as cantidad FROM owners
UNION ALL
SELECT 'Vehicles', count(*) FROM vehicles
UNION ALL
SELECT 'Rules', count(*) FROM rules;