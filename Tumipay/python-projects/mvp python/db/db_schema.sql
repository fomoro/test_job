-- Limpieza inicial (opcional, por si quieres reiniciar)
-- DROP TABLE IF EXISTS transactions;
-- DROP TABLE IF EXISTS accounts;
-- DROP TABLE IF EXISTS clients;

-- =============================================
-- 1. TABLA CLIENTES
-- =============================================
CREATE TABLE IF NOT EXISTS clients (
    client_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- 2. TABLA CUENTAS
-- =============================================
CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    account_number VARCHAR(50) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL, -- 'checking', 'savings'
    currency VARCHAR(3) DEFAULT 'COP',
    
    -- Estado de la cuenta (Regla de Negocio)
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'blocked')), 
    
    -- Manejo de dinero (Siempre NUMERIC, nunca FLOAT)
    balance NUMERIC(15, 2) DEFAULT 0.00 CHECK (balance >= 0),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Integridad Referencial
    CONSTRAINT fk_account_client FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- =============================================
-- 3. TABLA TRANSACCIONES (El Core)
-- =============================================
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    
    -- Relaciones
    client_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    
    -- Datos Financieros
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) NOT NULL,
    
    -- Orquestación (Patrones Strategy/Adapter)
    payment_method VARCHAR(50) NOT NULL, -- 'pse', 'credit_card', 'nequi'
    provider VARCHAR(50) NOT NULL,       -- 'payu', 'kushki', 'stripe'
    
    -- Auditoría del Adapter (Aquí guardamos lo que nos responde el proveedor externo)
    provider_reference VARCHAR(100),     
    
    -- CICLO DE VIDA (State Machine)
    -- Esto obliga a la BD a respetar tus estados definidos en el Enum de Python
    status VARCHAR(20) NOT NULL CHECK (status IN ('CREATED', 'VALIDATED', 'PROCESSED', 'FAILED')),
    status_message TEXT,
    
    -- SEGURIDAD: IDEMPOTENCIA
    -- La restricción UNIQUE impide físicamente crear duplicados
    idempotency_key VARCHAR(100) UNIQUE NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Llaves Foráneas
    CONSTRAINT fk_tx_client FOREIGN KEY (client_id) REFERENCES clients(client_id),
    CONSTRAINT fk_tx_account FOREIGN KEY (account_id) REFERENCES accounts(account_id)
);

-- Índices para optimizar consultas por cliente y fecha
CREATE INDEX idx_tx_client ON transactions(client_id);
CREATE INDEX idx_tx_created_at ON transactions(created_at);