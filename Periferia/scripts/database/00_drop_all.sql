/*
 * CCS - CENTRAL DE SEGUIMIENTO VEHICULAR
 * SCRIPT MAESTRO: ESQUEMA + DATOS + ÍNDICES
 * Versión: Final (High Performance)
 */

-- =================================================================================
-- 1. LIMPIEZA DE ENTORNO (Borra todo para iniciar limpio)
-- =================================================================================
DROP TABLE IF EXISTS alerts CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS rules CASCADE;
DROP TABLE IF EXISTS vehicles CASCADE;
DROP TABLE IF EXISTS owners CASCADE;
