# 🚀 TumiPay Transaction Mock - Features Checklist

Este documento detalla las capacidades técnicas, patrones de diseño y reglas de negocio implementadas en el simulador de procesamiento de pagos (PayIn).

## 1. Arquitectura y Patrones de Diseño
Implementación de principios de diseño de software para garantizar extensibilidad y desacoplamiento.

- [x] **Patrón Strategy:** Definición de una interfaz común (`PaymentGateway`) para estandarizar el procesamiento de pagos sin importar el proveedor.
- [x] **Patrón Adapter:** Implementación de adaptadores específicos para simular integraciones con **PayU**, **Kushki** y **Stripe**, cada uno con su propia lógica de traducción de datos.
- [x] **Patrón Factory:** Uso de una clase fábrica (`PaymentFactory`) para la instanciación dinámica del proveedor correcto en tiempo de ejecución, eliminando sentencias `if/else` complejas en el controlador.
- [x] **Separación de Capas (Lógica):** Distinción clara entre la capa de Controladores (API), Dominio (Modelos) e Infraestructura (Adaptadores Simulados).

## 2. Seguridad y Consistencia (Reliability)
Mecanismos para garantizar la integridad de las transacciones y evitar errores críticos.

- [x] **Idempotencia Estricta:** Implementación de llave de idempotencia vía Header (`x-idempotency-key`).
  - *Comportamiento:* Si se detecta una llave reutilizada, el sistema rechaza la petición inmediatamente (`409 Conflict`), previniendo cobros dobles.
- [x] **Manejo de Errores HTTP Estándar:**
  - `201 Created`: Transacción exitosa.
  - `400 Bad Request`: Datos inválidos o errores de validación.
  - `404 Not Found`: Cliente o recurso no existente.
  - `409 Conflict`: Violación de reglas de negocio (ej. Cuenta Bloqueada, Duplicado).
  - `500 Internal Server Error`: Fallos simulados en el proveedor externo.

## 3. Reglas de Negocio (Domain Logic)
Validaciones estrictas antes de permitir el movimiento de fondos.

- [x] **Integridad Referencial:** Validación de existencia del `client_id` y que el `account_id` destino realmente pertenezca a ese cliente.
- [x] **Estado de la Cuenta:** Bloqueo de operaciones si la cuenta destino no está en estado `active` (ej. rechazo de cuentas `blocked`).
- [x] **Límites Transaccionales:** Validación de montos positivos y tope máximo por transacción (simulado en 5M COP).
- [x] **Validación de Proveedores:** Verificación de que el `provider_id` y `payment_method_id` sean soportados por la plataforma.

## 4. Datos y Simulación
Estrategia de datos para facilitar pruebas manuales y de carga.

- [x] **Simulación Híbrida de Datos:**
  - **Cliente de Control (Fixed):** Usuario "Wolfan Tester" con IDs fijos para probar casos de éxito y error (cuenta bloqueada) determinísticos.
  - **Clientes Aleatorios (Faker):** Generación de usuarios random para simular volumen y variedad de datos.
- [x] **Persistencia Volátil (In-Memory):** Almacenamiento temporal de transacciones y llaves de idempotencia durante el ciclo de vida de la ejecución.
- [x] **Respuestas Enriquecidas:** El JSON de respuesta incluye referencias externas simuladas (ej. `payu-uuid`, `ticket-kushki`) para evidenciar el paso por los adaptadores.

---
*Generado para la Prueba Técnica de Líder Técnico - TumiPay*