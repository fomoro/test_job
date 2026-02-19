-- =================================================================================
-- 3. INSERTAR SEÑALES Y ALERTAS
-- =================================================================================

-- 1. Limpiar datos existentes
TRUNCATE TABLE signals, alerts RESTART IDENTITY CASCADE;

-- 2. Insertar 1000 señales de prueba
INSERT INTO signals (vehicle_id, timestamp, latitude, longitude, speed, heading, metadata)
SELECT 
    v.id,
    NOW() - (random() * interval '3 days'),
    4.6 + random() * 0.2,
    -74.1 + random() * 0.2,
    CASE v.type 
        WHEN 'TRUCK' THEN 40 + random() * 50
        WHEN 'CAR' THEN 30 + random() * 70
        WHEN 'MOTO' THEN 20 + random() * 40
    END,
    random() * 360,
    CASE 
        WHEN v.type = 'TRUCK' AND v.details->>'type' = 'reefer'
            THEN jsonb_build_object('cargo_temp', -10 + random() * 15)
        WHEN v.type = 'CAR' AND v.id LIKE 'TAXI-%'
            THEN jsonb_build_object('panic_button', random() > 0.99)
        WHEN v.type = 'TRUCK'
            THEN jsonb_build_object('door_status', CASE WHEN random() > 0.95 THEN 'open' ELSE 'closed' END)
        ELSE '{}'::jsonb
    END
FROM vehicles v
CROSS JOIN generate_series(1, 15)
ORDER BY random()
LIMIT 1000;

-- 3. Insertar 50 alertas de ejemplo
INSERT INTO alerts (vehicle_id, rule_id, signal_id, timestamp, message, action_taken)
SELECT 
    v.id,
    r.id,
    s.id,
    NOW() - (random() * interval '2 days'),
    CASE r.rule_type
        WHEN 'MAX_SPEED' THEN CONCAT('Vehículo ', v.id, ' excedió velocidad (', 
                                     ROUND(80 + random() * 30)::text, 'km/h > ', r.comparison_value, 'km/h)')
        WHEN 'PANIC_BUTTON' THEN CONCAT('Botón de pánico activado en ', v.id)
        WHEN 'TEMP_MAX' THEN CONCAT('Temperatura crítica en camión refrigerado ', v.id)
        ELSE CONCAT('Regla ', r.rule_type, ' activada para ', v.id)
    END,
    CASE r.action_type
        WHEN 'NOTIFY_POLICE' THEN 'Llamada a autoridades realizada'
        WHEN 'NOTIFY_OWNER' THEN 'SMS enviado al dueño'
        WHEN 'SMS_OWNER' THEN 'Mensaje SMS enviado'
        WHEN 'LOG_ONLY' THEN 'Registrado en log del sistema'
        ELSE 'Acción ejecutada: ' || r.action_type
    END
FROM vehicles v
JOIN rules r ON v.id = r.vehicle_id
JOIN signals s ON v.id = s.vehicle_id
WHERE r.is_active = TRUE
ORDER BY random()
LIMIT 50;

-- 4. Verificar resultados
SELECT 'Señales' as tipo, COUNT(*) as cantidad FROM signals
UNION ALL
SELECT 'Alertas', COUNT(*) FROM alerts;