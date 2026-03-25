# 00 - Análisis Técnico: Billetera Digital de Alto Volumen 


**Autor:** Jonathan Wolfan Moreno Rodriguez 
**Fecha:** Marzo 2026  
**Contexto:** Prueba técnica - Arquitectura de Soluciones

---

## 1. Contexto del Negocio

Una empresa fintech planea lanzar una **billetera digital** para el mercado latinoamericano.

**Objetivos estratégicos:**
- Habilitar pagos, transferencias y manejo de efectivo
- **Alta disponibilidad** (99.95% SLO)
- **Bajo costo operativo** (escalamiento horizontal, consumo bajo demanda)
- **Cumplimiento regulatorio** (auditoría, retención 7 años, protección de datos)

**Comportamiento esperado:**
- Crecimiento progresivo
- Picos altos en quincenas, fines de semana y promociones

---

## 2. Requisitos Funcionales

| # | Funcionalidad | Detalle |
|---|---------------|---------|
| **1** | Gestión de cuentas | Consulta de saldo, movimientos, historial transaccional |
| **2** | Transferencias internas | Entre usuarios de la billetera. Confirmación inmediata |
| **3** | Transferencias interbancarias | Envío/recepción desde banco externo. Estados: pendiente, completada, fallida |
| **4** | Consignaciones y retiros | Vía corresponsales. Validaciones previas y confirmaciones |
| **5** | Notificaciones | Integración con sistema legacy existente (vía evento) |

---

## 3. Requisitos No Funcionales

| # | Requisito | Métrica / Detalle |
|---|-----------|-------------------|
| **1** | Escalabilidad | Ver volúmenes sección 4 |
| **2** | Disponibilidad | **SLO 99.95%** → downtime máximo 4.38 horas/año |
| **3** | Consistencia | Dinero no se pierde ni duplica. Identificar fuerte vs eventual |
| **4** | Seguridad | Autenticación, autorización, protección datos sensibles, prevención fraudes |
| **5** | Observabilidad | Métricas, logs, trazas. Detección de fallas y cuellos de botella |

---

## 4. Volúmenes de Transacciones

| Tipo | Volumen Diario | Pico Esperado |
|------|----------------|---------------|
| Transferencias internas | 1,000,000 | 2x (quincenas) |
| Transferencias interbancarias | 600,000 | 1.5x (fines de semana) |
| Consignaciones y retiros | 2,000,000 | 3x (promociones) |
| **Total** | **3,600,000** | **~7,200,000 pico** |

**Promedio:** 41.6 tx/seg  
**Pico:** ~83 tx/seg

---

## 5. Entregables Solicitados

| # | Entregable | Documento |
|---|------------|-----------|
| **1** | Arquitectura de alto nivel + componentes | `01-architecture-high-level.md` |
| **2** | Patrones de arquitectura | `01-architecture-high-level.md` |
| **3** | Diseño de persistencia | `02-persistence-design.md` |
| **4** | Flujo transferencia interbancaria | `03-interbank-transfer-flow.md` |
| **5** | Trade-offs | `04-tradeoffs-analysis.md` |

**Soporte transversal:** `05-deployment-security-observability.md`

---

## 6. Patrones de Arquitectura Aplicados

| Patrón | Dónde | Por qué |
|--------|-------|---------|
| **Microservicios** | División por dominio (Account, Transfer, Cash, Notification) | Escalamiento independiente por volumen asimétrico |
| **CQRS** | Account Service | Lecturas (Redis) vs escrituras (SQL). Ratio 10:1 |
| **Saga Coreográfica** | Transferencia interbancaria | Consistencia distribuida sin 2PC. Bancos externos no soportan transacciones distribuidas |
| **Outbox Pattern** | Publicación de eventos | Eventos en misma transacción ACID. Garantía de entrega |
| **Circuit Breaker** | Bank Adapters | Resiliencia ante fallos de terceros. Evita cascading failures |
| **Cache-Aside** | Consultas de saldo | Redis first (TTL 5s). Fallback a SQL |

---

## 7. Matriz de Consistencia: Fuerte vs Eventual

| Operación | Consistencia | Estrategia |
|-----------|--------------|------------|
| Débito/Crédito | **Fuerte** | ACID en SQL con pessimistic lock |
| Transferencia interna | **Fuerte** | Transacción ACID origen y destino |
| Transferencia interbancaria | **Eventual con compensación** | Saga coreográfica. Fallback reversa fondos |
| Consulta de saldo | **Eventual (2-5s)** | Redis cache TTL 5s |
| Historial transaccional | **Eventual** | Cosmos DB, alimentación asíncrona |
| Notificaciones | **Eventual** | Service Bus con retries y dead-letter |

---

## 8. Componentes Azure por Capa

| Capa | Componentes Clave |
|------|-------------------|
| **Entrada** | Azure Front Door + WAF, API Management |
| **Aplicación** | AKS (microservicios), Service Bus (eventos) |
| **Persistencia** | Azure SQL (ACID), Cosmos DB (historial), Redis (caché TTL 5s) |
| **Seguridad** | Entra ID, Key Vault, Private Links |
| **Observabilidad** | Application Insights, Azure Monitor, Log Analytics |
| **CI/CD** | Azure DevOps, Azure Container Registry |

---

## 9. Resumen de Decisiones Clave

| Decisión | Ganancia | Sacrificio |
|----------|----------|------------|
| Microservicios en AKS | Escalamiento independiente | Complejidad operativa |
| Saga coreográfica | Sin 2PC con bancos externos | Consistencia eventual |
| CQRS + Redis TTL 5s | Lecturas rápidas, protege SQL | Consistencia eventual en saldos |
| Outbox Pattern + Worker | Eventos no se pierden | Latencia adicional (ms) |
| Multi-db (SQL + Cosmos + Redis) | Cada workload optimizado | Complejidad infraestructura |
| Circuit Breaker | Protege recursos internos | Ventana de rechazo post-fallo (60s) |
| Pessimistic Locking | Integridad financiera absoluta | Concurrencia reducida |

---

## 10. Resumen Ejecutivo

**Puntos Clave para Sustentación:**

1. **Microservicios justificados por volumen asimétrico**: 2M consignaciones, 1M internas, 600K interbancarias. Escalamiento independiente.

2. **Saga coreográfica vs 2PC**: Bancos externos no soportan transacciones distribuidas. Saga con compensación automática.

3. **CQRS por ratio read/write 10:1**: Consultas de saldo más frecuentes que escrituras. Redis protege SQL.

4. **Outbox Pattern garantiza eventos**: Notificaciones no pueden perderse. Evento en misma transacción ACID.

5. **Circuit Breaker es crítico**: Fallo en banco externo no colapsa el sistema.

6. **Persistencia políglota**: SQL para dinero (ACID), Cosmos DB para historial (throughput), Redis para caché (latencia).

7. **SLO 99.95% alcanzable**: Multi-region + AKS + Azure SQL Hyperscale + failover automático.

---

**Documentos Relacionados:**
- [01-architecture-high-level.md](./01-architecture-high-level.md) → omponentes, patrones, TTL alineado (5s)
- [02-persistence-design.md](./02-persistence-design.md) → Modelo de datos, particionamiento
- [03-interbank-transfer-flow.md](./03-interbank-transfer-flow.md) → Flujo Saga detallado
- [04-tradeoffs-analysis.md](./04-tradeoffs-analysis.md) → ADRs completos
- [05-deployment-security-observability.md](./05-deployment-security-observability.md) → CI/CD, seguridad