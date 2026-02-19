# 🧪 Guía de Pruebas Integral (End-to-End Testing)

Esta guía detalla los pasos para validar todos los endpoints y reglas de negocio del simulador TumiPay. Sigue estos pasos en la interfaz de Swagger (`http://127.0.0.1:8000/docs`) para certificar la calidad del componente.

## 📋 Datos Maestros para Pruebas
Utilice estos datos fijos preconfigurados en el Mock para garantizar resultados predecibles y reproducibles.

| Recurso | ID / Valor | Estado Esperado |
| :--- | :--- | :--- |
| **Cliente Test** | `cli-123-test` | Cliente existente validado |
| **Cuenta Activa** | `acc-active-001` | ✅ Cuenta habilitada para recibir fondos |
| **Cuenta Bloqueada** | `acc-blocked-999` | ⛔ Cuenta restringida (Regla de Negocio) |
| **Límite Máximo** | `5,000,000` | Tope transaccional permitido |

---

## 1️⃣ Endpoint: Listar Clientes
**Objetivo:** Verificar la disponibilidad del servicio y la integridad de los datos maestros.

### ✅ Caso 1.1: Obtener lista completa
* **Método:** `GET`
* **URL:** `/api/v1/clients`
* **Acción:** Ejecutar sin parámetros.
* **Resultado Esperado:** `200 OK`.
    * El cuerpo de respuesta debe ser una lista JSON.
    * Debe contener obligatoriamente al cliente de control: `cli-123-test`.

---

## 2️⃣ Endpoint: Crear Transacción (Core)
**Objetivo:** Validar la orquestación, integración de adaptadores, reglas de negocio e idempotencia.

### ✅ Caso 2.1: Pago Exitoso con PayU (Adapter A)
Verifica el flujo feliz utilizando el adaptador de PayU.
* **Método:** `POST` `/api/v1/payins`
* **Header (Required):** `x-idempotency-key: key-payu-001`
* **Body:**
    ```json
    {
      "client_id": "cli-123-test",
      "account_id": "acc-active-001",
      "amount": 50000,
      "currency": "COP",
      "payment_method_id": "pse",
      "provider_id": "payu"
    }
    ```
* **Resultado:** `201 Created`.
    * Validar campo `provider_reference`: debe iniciar con `payu-...`.

### ✅ Caso 2.2: Pago Exitoso con Kushki (Adapter B)
Verifica el polimorfismo cambiando el proveedor.
* **Header:** `x-idempotency-key: key-kushki-001`
* **Body:** Usar el mismo JSON del Caso 2.1, pero cambiar `provider_id` a `"kushki"`.
* **Resultado:** `201 Created`.
    * Validar campo `provider_reference`: debe iniciar con `ticket-...`.

### ⛔ Caso 2.3: Error de Idempotencia (Duplicado)
Verifica la protección contra cobros dobles.
* **Acción:** Vuelva a ejecutar el **Caso 2.1** exactamente igual (misma Key y mismo Body).
* **Resultado:** `409 Conflict`.
    * Mensaje: *"Conflicto: Llave ya procesada..."*

### ⛔ Caso 2.4: Regla de Negocio - Cuenta Bloqueada
Verifica que no se procesen pagos a cuentas con problemas de compliance.
* **Header:** `x-idempotency-key: key-fail-blocked`
* **Body:** Cambie `account_id` a `"acc-blocked-999"`.
* **Resultado:** `409 Conflict`.
    * Mensaje: *"Cuenta blocked: No recibe fondos"*.

### ⛔ Caso 2.5: Regla de Negocio - Exceso de Límite
Verifica los topes financieros de seguridad.
* **Header:** `x-idempotency-key: key-fail-limit`
* **Body:** Cambie `amount` a `6000000` (6 Millones).
* **Resultado:** `400 Bad Request`.
    * Mensaje: *"Monto fuera de límites"*.

### ⛔ Caso 2.6: Validación de Integridad - Proveedor Inválido
Verifica que la Factory rechace proveedores no configurados.
* **Header:** `x-idempotency-key: key-fail-provider`
* **Body:** Cambie `provider_id` a `"paypal"` (No soportado).
* **Resultado:** `400 Bad Request`.
    * Mensaje: *"Proveedor inválido"*.

---

## 3️⃣ Endpoint: Consultar Transacción
**Objetivo:** Verificar la persistencia y recuperación de datos.

### ✅ Caso 3.1: Consultar Transacción Existente
* **Requisito:** Copie el `transaction_id` obtenido en la respuesta del **Caso 2.1**.
* **Método:** `GET`
* **URL:** `/api/v1/payins/{transaction_id_copiado}`
* **Resultado:** `200 OK`.
    * Verificar que `status` sea `PROCESSED`.
    * Verificar que `amount` sea `50000`.

### ⛔ Caso 3.2: Consultar Transacción Inexistente
* **Método:** `GET`
* **URL:** `/api/v1/payins/00000000-0000-0000-0000-000000000000`
* **Resultado:** `404 Not Found`.
    * Mensaje: *"Transacción no encontrada"*.