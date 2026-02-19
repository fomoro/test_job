# Consultas SQL Estratégicas para PostgreSQL

**10 consultas SQL estratégicas**, organizadas por función: **Soporte**, **Negocio** y **Auditoría**.

---

## 🔍 Soporte y Operaciones (Troubleshooting)

Consultas útiles cuando un usuario reporta: “mi pago falló”.

### 1. Historial completo de un cliente (Visión 360)
Muestra todas las transacciones de un usuario con nombres legibles de proveedor y método de pago.

```sql
SELECT 
    t.created_at,
    t.status,
    t.amount,
    t.currency,
    p.name AS provider,
    pm.name AS method,
    t.status_message
FROM transactions t
JOIN clients c ON t.client_id = c.client_id
JOIN providers p ON t.provider_id = p.provider_id
JOIN payment_methods pm ON t.payment_method_id = pm.method_id
WHERE c.email = 'wolfan@tumipay.com' -- Cambiar por el email a buscar
ORDER BY t.created_at DESC;
```

---

### 2. Diagnóstico de fallos
Detecta causas recurrentes de pagos rechazados.

```sql
SELECT 
    status_message, 
    provider_id,
    COUNT(*) AS total_failures
FROM transactions
WHERE status = 'FAILED'
GROUP BY status_message, provider_id
ORDER BY total_failures DESC;
```

### 3. Transacciones “zombie”
Transacciones en `CREATED` o `VALIDATED` por más de 10 minutos.

```sql
SELECT transaction_id, created_at, status, provider_id
FROM transactions
WHERE status IN ('CREATED', 'VALIDATED')
  AND created_at < NOW() - INTERVAL '10 minutes';
```

---

## 📊 Inteligencia de Negocio (BI & Finanzas)

Consultas típicas para reportes ejecutivos.

### 4. Volumen transaccional diario por estado

```sql
SELECT 
    DATE(created_at) AS fecha,
    status,
    COUNT(*) AS cantidad_tx,
    SUM(amount) AS volumen_total
FROM transactions
GROUP BY DATE(created_at), status
ORDER BY fecha DESC, status;
```

---

### 5. Top 5 clientes por volumen procesado (VIPs)

```sql
SELECT 
    c.full_name,
    COUNT(t.transaction_id) AS total_pagos,
    SUM(t.amount) AS total_dinero_movido
FROM transactions t
JOIN clients c ON t.client_id = c.client_id
WHERE t.status = 'PROCESSED'
GROUP BY c.full_name
ORDER BY total_dinero_movido DESC
LIMIT 5;
```

---

### 6. Participación por proveedor (Share of Wallet)

```sql
SELECT 
    provider_id,
    COUNT(*) AS total_tx,
    SUM(amount) AS volumen_procesado,
    ROUND(
        (COUNT(*) * 100.0 / 
        (SELECT COUNT(*) FROM transactions WHERE status = 'PROCESSED')), 
        2
    ) AS porcentaje_uso
FROM transactions
WHERE status = 'PROCESSED'
GROUP BY provider_id;
```

---

## 🛡️ Auditoría y Seguridad

Consultas para consistencia, control y riesgo.

### 7. Auditoría de idempotencia
Verifica que no existan claves duplicadas.

```sql
SELECT idempotency_key, COUNT(*)
FROM transactions
GROUP BY idempotency_key
HAVING COUNT(*) > 1;
-- Debe retornar 0 filas si el constraint UNIQUE funciona correctamente.
```

---

### 8. Conciliación bancaria
Listado para cruzar con extractos del proveedor.

```sql
SELECT 
    transaction_id,
    provider_id,
    provider_reference,
    amount,
    created_at
FROM transactions
WHERE status = 'PROCESSED'
  AND provider_id = 'payu' -- Cambiar según proveedor
  AND created_at BETWEEN '2023-10-01' AND '2023-10-31';
```

---

### 9. Clientes con cuentas bloqueadas y actividad reciente

```sql
SELECT DISTINCT 
    c.full_name, 
    c.email, 
    a.status AS estado_cuenta
FROM transactions t
JOIN accounts a ON t.account_id = a.account_id
JOIN clients c ON t.client_id = c.client_id
WHERE a.status = 'blocked'
  AND t.created_at > NOW() - INTERVAL '24 hours';
```

---

### 10. Balance total del ecosistema (Liability)

```sql
SELECT 
    currency,
    SUM(balance) AS pasivo_total_empresa
FROM accounts
WHERE status = 'active'
GROUP BY currency;
```

---

Con este set de queries cubres **la mayoría de escenarios reales**: soporte, métricas de negocio y auditoría. Ideal para guardarlo junto con los scripts del esquema o como material de entrevista técnica.