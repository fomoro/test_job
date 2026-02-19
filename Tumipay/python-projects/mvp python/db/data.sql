-- 1. Crear Cliente
INSERT INTO clients (client_id, full_name, email)
VALUES ('cli-123-test', 'Wolfan Tester', 'wolfan@tumipay.com')
ON CONFLICT (client_id) DO NOTHING;

-- 2. Crear Cuenta ACTIVA (Para el Happy Path)
INSERT INTO accounts (account_id, client_id, account_number, account_type, status, currency, balance)
VALUES ('acc-active-001', 'cli-123-test', '111-222-333', 'checking', 'active', 'COP', 1000000.00)
ON CONFLICT (account_id) DO NOTHING;

-- 3. Crear Cuenta BLOQUEADA (Para probar el estado FAILED)
INSERT INTO accounts (account_id, client_id, account_number, account_type, status, currency, balance)
VALUES ('acc-blocked-999', 'cli-123-test', '999-888-777', 'savings', 'blocked', 'COP', 50.00)
ON CONFLICT (account_id) DO NOTHING;