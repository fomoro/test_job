-- =============================================
-- 0. ELIMINAR TABLAS EXISTENTES
-- =============================================

DROP TABLE IF EXISTS idempotency_keys;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS payment_methods;
DROP TABLE IF EXISTS providers;

-- =============================================
-- 1. CREAR TABLAS EN ORDEN CORRECTO
-- =============================================

-- 1.1 Catálogos (sin dependencias)
CREATE TABLE providers (
    provider_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE payment_methods (
    method_id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1.2 Clientes
CREATE TABLE clients (
    client_id VARCHAR(50) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1.3 Cuentas (depende de clients)
CREATE TABLE accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    account_number VARCHAR(50) UNIQUE NOT NULL,
    account_type VARCHAR(20) NOT NULL, 
    status VARCHAR(20) NOT NULL CHECK (status IN ('active', 'blocked')), 
    balance NUMERIC(15, 2) DEFAULT 0.00 CHECK (balance >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_account_client FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

-- 1.4 Transacciones (depende de todos)
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'COP',
    
    payment_method_id VARCHAR(20) NOT NULL,
    provider_id VARCHAR(20) NOT NULL,
    
    provider_reference VARCHAR(100),     
    status VARCHAR(20) NOT NULL CHECK (status IN ('CREATED', 'VALIDATED', 'PROCESSED', 'FAILED')),
    status_message TEXT,
    
    idempotency_key VARCHAR(100) UNIQUE NOT NULL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_tx_client FOREIGN KEY (client_id) REFERENCES clients(client_id),
    CONSTRAINT fk_tx_account FOREIGN KEY (account_id) REFERENCES accounts(account_id),
    CONSTRAINT fk_tx_method FOREIGN KEY (payment_method_id) REFERENCES payment_methods(method_id),
    CONSTRAINT fk_tx_provider FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);

-- 1.5 Idempotencia (depende de transactions)
CREATE TABLE idempotency_keys (
    idempotency_key VARCHAR(100) PRIMARY KEY,
    transaction_id VARCHAR(50),
    status VARCHAR(20) NOT NULL DEFAULT 'PROCESSING' 
        CHECK (status IN ('PROCESSING', 'COMPLETED', 'FAILED')),
    request_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT fk_idempotency_transaction FOREIGN KEY (transaction_id) 
        REFERENCES transactions(transaction_id) ON DELETE SET NULL
);

-- =============================================
-- 2. DATOS INICIALES DE CONFIGURACIÓN
-- =============================================

INSERT INTO providers (provider_id, name, is_active) VALUES
    ('payu', 'PayU', TRUE),
    ('kushki', 'Kushki', TRUE),
    ('stripe', 'Stripe', TRUE);

INSERT INTO payment_methods (method_id, name) VALUES
    ('pse', 'PSE'),
    ('credit_card', 'Tarjeta de Crédito'),
    ('nequi', 'Nequi');

-- =============================================
-- 3. USUARIO DE CONTROL (Para pruebas de QA)
-- =============================================

INSERT INTO clients (client_id, full_name, email) VALUES 
('cli-123-test', 'Wolfan Tester', 'wolfan@tumipay.com');

INSERT INTO accounts (account_id, client_id, account_number, account_type, status, balance) VALUES 
('acc-active-001', 'cli-123-test', '111-222-000', 'checking', 'active', 1000000.00),
('acc-blocked-999', 'cli-123-test', '999-888-000', 'savings', 'blocked', 50.00);

-- =============================================
-- 4. POBLACIÓN MASIVA (30 Clientes Nuevos)
-- =============================================

INSERT INTO clients (client_id, full_name, email) VALUES
('cli-001', 'Ana Maria Perez', 'ana.perez@example.com'),
('cli-002', 'Carlos Gomez', 'carlos.gomez@example.com'),
('cli-003', 'Diana Trujillo', 'diana.trujillo@example.com'),
('cli-004', 'Eduardo Diaz', 'eduardo.diaz@example.com'),
('cli-005', 'Fernanda Lopez', 'fernanda.lopez@example.com'),
('cli-006', 'Gabriel Garcia', 'gabriel.garcia@example.com'),
('cli-007', 'Hector Ramirez', 'hector.ramirez@example.com'),
('cli-008', 'Isabel Torres', 'isabel.torres@example.com'),
('cli-009', 'Juan Rodriguez', 'juan.rodriguez@example.com'),
('cli-010', 'Karen Martinez', 'karen.martinez@example.com'),
('cli-011', 'Luis Hernandez', 'luis.hernandez@example.com'),
('cli-012', 'Maria Gonzalez', 'maria.gonzalez@example.com'),
('cli-013', 'Natalia Castro', 'natalia.castro@example.com'),
('cli-014', 'Oscar Vargas', 'oscar.vargas@example.com'),
('cli-015', 'Paula Rios', 'paula.rios@example.com'),
('cli-016', 'Quintin Tarantino', 'quintin.t@example.com'),
('cli-017', 'Rosa Melano', 'rosa.melano@example.com'),
('cli-018', 'Santiago Silva', 'santiago.silva@example.com'),
('cli-019', 'Tatiana Mendoza', 'tatiana.mendoza@example.com'),
('cli-020', 'Ulises Bueno', 'ulises.bueno@example.com'),
('cli-021', 'Valentina Rojas', 'valentina.rojas@example.com'),
('cli-022', 'Walter White', 'walter.white@breaking.com'),
('cli-023', 'Ximena Sariñana', 'ximena.s@example.com'),
('cli-024', 'Yuri Gagarin', 'yuri.space@example.com'),
('cli-025', 'Zoe Saldana', 'zoe.avatar@example.com'),
('cli-026', 'Andres Cepeda', 'andres.cepeda@music.com'),
('cli-027', 'Shakira Mebarak', 'shakira@music.com'),
('cli-028', 'Juanes Aristizabal', 'juanes@music.com'),
('cli-029', 'Sofia Vergara', 'sofia.vergara@hollywood.com'),
('cli-030', 'James Rodriguez', 'james.10@soccer.com');

-- =============================================
-- 5. POBLACIÓN MASIVA DE CUENTAS
-- =============================================

INSERT INTO accounts (account_id, client_id, account_number, account_type, status, balance) VALUES
-- Cuentas Activas
('acc-001', 'cli-001', '100-001', 'savings', 'active', 500000.00),
('acc-002', 'cli-002', '100-002', 'checking', 'active', 120000.00),
('acc-003', 'cli-003', '100-003', 'savings', 'active', 75000.00),
('acc-004', 'cli-004', '100-004', 'checking', 'active', 2500000.00),
('acc-005', 'cli-005', '100-005', 'savings', 'active', 30000.00),
('acc-006', 'cli-006', '100-006', 'checking', 'active', 890000.00),
('acc-007', 'cli-007', '100-007', 'savings', 'active', 450000.00),
('acc-008', 'cli-008', '100-008', 'checking', 'active', 15000.00),
('acc-009', 'cli-009', '100-009', 'savings', 'active', 900000.00),
('acc-010', 'cli-010', '100-010', 'checking', 'active', 110000.00),
('acc-011', 'cli-011', '100-011', 'savings', 'active', 600000.00),
('acc-012', 'cli-012', '100-012', 'checking', 'active', 200000.00),
('acc-013', 'cli-013', '100-013', 'savings', 'active', 35000.00),
('acc-014', 'cli-014', '100-014', 'checking', 'active', 78000.00),
('acc-015', 'cli-015', '100-015', 'savings', 'active', 95000.00),
('acc-016', 'cli-016', '100-016', 'checking', 'active', 10000000.00),
('acc-017', 'cli-017', '100-017', 'savings', 'active', 5000.00),
('acc-018', 'cli-018', '100-018', 'checking', 'active', 80000.00),
('acc-019', 'cli-019', '100-019', 'savings', 'active', 420000.00),
('acc-020', 'cli-020', '100-020', 'checking', 'active', 330000.00),
('acc-021', 'cli-021', '100-021', 'savings', 'active', 125000.00),
('acc-022', 'cli-022', '100-022', 'checking', 'active', 999999.00),
('acc-023', 'cli-023', '100-023', 'savings', 'active', 67000.00),
('acc-024', 'cli-024', '100-024', 'checking', 'active', 0.00),
('acc-025', 'cli-025', '100-025', 'savings', 'active', 250000.00),
('acc-026', 'cli-026', '100-026', 'checking', 'active', 1500000.00),
('acc-027', 'cli-027', '100-027', 'savings', 'active', 8500000.00),
('acc-028', 'cli-028', '100-028', 'checking', 'active', 450000.00),
('acc-029', 'cli-029', '100-029', 'savings', 'active', 7000000.00),
('acc-030', 'cli-030', '100-030', 'checking', 'active', 3000000.00),

-- Cuentas Bloqueadas o Adicionales
('acc-001-B', 'cli-001', '100-001-B', 'savings', 'blocked', 100.00),
('acc-030-B', 'cli-030', '100-030-B', 'savings', 'blocked', 0.00);

-- =============================================
-- 6. SIMULACIÓN DE HISTORIAL (Transacciones pasadas)
-- =============================================

INSERT INTO transactions (
    transaction_id, client_id, account_id, amount, currency, 
    payment_method_id, provider_id, provider_reference, status, idempotency_key
) VALUES
('tx-seed-001', 'cli-001', 'acc-001', 20000, 'COP', 'nequi', 'payu', 'ref-001', 'PROCESSED', 'key-seed-001'),
('tx-seed-002', 'cli-002', 'acc-002', 50000, 'COP', 'pse', 'kushki', 'ref-002', 'PROCESSED', 'key-seed-002'),
('tx-seed-003', 'cli-030', 'acc-030-B', 10000, 'COP', 'credit_card', 'stripe', NULL, 'FAILED', 'key-seed-003');

-- =============================================
-- 7. TRANSACCIONES VARIADAS PARA TESTING
-- =============================================

-- A. Transacciones para "Wolfan Tester"
INSERT INTO transactions (transaction_id, client_id, account_id, amount, currency, payment_method_id, provider_id, provider_reference, status, status_message, idempotency_key, created_at) VALUES
('tx-wolfan-01', 'cli-123-test', 'acc-active-001', 50000.00, 'COP', 'pse', 'payu', 'payu-ref-001', 'PROCESSED', 'Aprobado', 'key-w-01', NOW() - INTERVAL '2 days'),
('tx-wolfan-02', 'cli-123-test', 'acc-active-001', 20000.00, 'COP', 'credit_card', 'stripe', 'ch_stripe_01', 'PROCESSED', 'Succeeded', 'key-w-02', NOW() - INTERVAL '1 day'),
('tx-wolfan-03', 'cli-123-test', 'acc-active-001', 1500000.00, 'COP', 'nequi', 'kushki', NULL, 'FAILED', 'Fondos insuficientes', 'key-w-03', NOW());

-- B. Transacción "Zombie" (Stuck Transaction)
INSERT INTO transactions (transaction_id, client_id, account_id, amount, currency, payment_method_id, provider_id, provider_reference, status, status_message, idempotency_key, created_at) VALUES
('tx-zombie-01', 'cli-005', 'acc-005', 45000.00, 'COP', 'pse', 'payu', NULL, 'CREATED', NULL, 'key-zombie-01', NOW() - INTERVAL '30 minutes');

-- C. Volumen para Reportes
INSERT INTO transactions (transaction_id, client_id, account_id, amount, currency, payment_method_id, provider_id, provider_reference, status, idempotency_key, created_at) VALUES
('tx-vol-01', 'cli-001', 'acc-001', 100000.00, 'COP', 'nequi', 'payu', 'ref-vol-01', 'PROCESSED', 'key-v-01', NOW()),
('tx-vol-02', 'cli-002', 'acc-002', 200000.00, 'COP', 'credit_card', 'stripe', 'ref-vol-02', 'PROCESSED', 'key-v-02', NOW()),
('tx-vol-03', 'cli-003', 'acc-003', 50000.00, 'COP', 'pse', 'kushki', 'ref-vol-03', 'PROCESSED', 'key-v-03', NOW()),
('tx-vol-04', 'cli-004', 'acc-004', 300000.00, 'COP', 'nequi', 'payu', 'ref-vol-04', 'PROCESSED', 'key-v-04', NOW()),
('tx-vol-05', 'cli-001', 'acc-001', 50000.00, 'COP', 'pse', 'payu', 'ref-vol-05', 'FAILED', 'key-v-05', NOW());

-- =============================================
-- 8. ÍNDICES PARA MEJOR PERFORMANCE
-- =============================================

-- Índices para transactions
CREATE INDEX idx_transactions_client_id ON transactions(client_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_idempotency_key ON transactions(idempotency_key);

-- Índices para idempotency_keys
CREATE INDEX idx_idempotency_created_at ON idempotency_keys(created_at);
CREATE INDEX idx_idempotency_status ON idempotency_keys(status);
CREATE INDEX idx_idempotency_transaction_id ON idempotency_keys(transaction_id);

-- Índices para clients
CREATE INDEX idx_clients_email ON clients(email);

-- Índices para accounts
CREATE INDEX idx_accounts_number ON accounts(account_number);
CREATE INDEX idx_accounts_client_id ON accounts(client_id);
CREATE INDEX idx_accounts_status ON accounts(status);

-- =============================================
-- 9. VERIFICACIÓN DE DATOS
-- =============================================

DO $$ 
BEGIN
    RAISE NOTICE '✅ Base de datos configurada exitosamente';
    RAISE NOTICE '📊 Resumen de datos:';
    RAISE NOTICE '   - Proveedores: %', (SELECT COUNT(*) FROM providers);
    RAISE NOTICE '   - Métodos de pago: %', (SELECT COUNT(*) FROM payment_methods);
    RAISE NOTICE '   - Clientes: %', (SELECT COUNT(*) FROM clients);
    RAISE NOTICE '   - Cuentas: %', (SELECT COUNT(*) FROM accounts);
    RAISE NOTICE '   - Transacciones: %', (SELECT COUNT(*) FROM transactions);
END $$;


-- Verificar que todo funciona
--SELECT * FROM clients WHERE client_id = 'cli-123-test';
--SELECT * FROM transactions WHERE client_id = 'cli-123-test';
--SELECT COUNT(*) as total_transacciones FROM transactions;