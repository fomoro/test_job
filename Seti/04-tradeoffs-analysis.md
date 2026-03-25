# 04 - Análisis de Trade-offs y Decisiones (ADRs) 

**Contexto:** Billetera Digital de Alto Volumen (3.6M tx/día, SLO 99.95%)

Cada decisión arquitectónica implica un balance. Este documento registra explícitamente qué se gana y qué se sacrifica.

---

## Resumen de Decisiones (ADRs)

| ADR | Decisión Adoptada |
|:---|:---|
| **ADR-001** | Microservicios en Azure Kubernetes Service (AKS) |
| **ADR-002** | Saga Coreográfica con Azure Service Bus |
| **ADR-003** | CQRS con Redis (TTL 5s) |
| **ADR-004** | Outbox Pattern con Worker polling en AKS |
| **ADR-005** | Persistencia Políglota (SQL + Cosmos DB + Redis) |
| **ADR-006** | Circuit Breaker + Retry exponencial limitado |
| **ADR-007** | Pessimistic Locking para débitos/créditos |
| **ADR-008** | Redis TTL 5 segundos para saldos |
| **ADR-009** | Particionamiento Hash (account) + Range (ledger) |

---

## Detalle de Decisiones

### ADR-001: Microservicios vs Monolito

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **Escalabilidad** | Escalamiento independiente por dominio | Complejidad operativa (orquestación, service discovery) |
| **Resiliencia** | Fallos aislados entre servicios | Latencia de red entre servicios (5-10ms) |

**Decisión:** Microservicios en AKS ✅

---

### ADR-002: Saga Coreográfica vs Saga Orquestada vs 2PC

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **Acoplamiento** | Servicios desacoplados. Sin cuello de botella central. | Visibilidad limitada. Requiere tracing distribuido. |
| **Consistencia** | No depende de 2PC con bancos externos. | Consistencia eventual. Requiere compensaciones. |

**Decisión:** Saga Coreográfica con Service Bus ✅

---

### ADR-003: CQRS vs CRUD Tradicional

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **Performance** | Redis absorbe ~90% lecturas. SQL dedicado a escrituras. | Consistencia eventual. Saldo visible puede tener 2-5s de desfase (TTL 5s). |
| **Escalabilidad** | Read y Write escalan independientemente. | Complejidad de sincronización vía eventos. |

**Decisión:** CQRS con Redis TTL 5s ✅

---

### ADR-004: Outbox Pattern vs Publicación Directa

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **Garantía de entrega** | *At-least-once* garantizado. Evento no se pierde si Service Bus falla. | Mayor complejidad. Requiere tabla `OutboxEvents` + Worker polling. |
| **Consistencia** | Evento en misma transacción ACID que operación financiera. | Latencia adicional (milisegundos) vs publicación directa. |

**Decisión:** Outbox Pattern con Worker polling en AKS ✅

---

### ADR-005: Persistencia Políglota vs Base de Datos Única

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **Optimización** | Cada workload en motor ideal: SQL (ACID), Cosmos (throughput), Redis (latencia sub-ms). | Complejidad operativa. Dominio de múltiples tecnologías. |
| **Costo a escala** | Se escala solo el componente con estrés. | Costo base inicial más alto (3 servicios PaaS). |

**Decisión:** Multi-db Políglota ✅

---

### ADR-006: Circuit Breaker vs Retry Infinito

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **Resiliencia** | Protege recursos internos (hilos AKS). Fail-fast si banco externo falla. | Latencia en recuperación. 60s de ventana con circuito abierto post-fallo. |
| **Retry controlado** | 4 intentos con exponential backoff cubren fallos transitorios. | Fallos persistentes requieren dead-letter manual. |

**Decisión:** Circuit Breaker + Retry exponencial (máx 4 intentos) ✅

---

### ADR-007: Pessimistic Locking vs Optimistic Locking

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **Integridad** | Garantía absoluta sin condición de carrera. `SELECT ... FOR UPDATE`. | Concurrencia reducida. Transacciones se serializan por cuenta. |
| **Aplicabilidad** | Ratio lectura/escritura 10:1. Contención baja en escrituras. | Aceptable porque carga principal es lecturas en caché. |

**Decisión:** Pessimistic Locking para débitos/créditos ✅

---

### ADR-008: Redis TTL para Saldos

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **TTL 5s** | Consistencia aceptable. Error de saldo visible dura máx 5s. | Más cache misses. Algunas consultas extras a SQL. |
| **TTL largo (>60s)** | Protección alta a SQL. | Consistencia débil. Usuario ve saldo desactualizado >1 min. |

**Decisión:** TTL 5 segundos ✅

---

### ADR-009: Particionamiento Hash vs Range

| Aspecto | Ganancia | Sacrificio |
|---------|----------|------------|
| **Hash (account)** | Distribución equitativa. Queries siempre por cliente (eficiente). | Consultas agregadas complejas (requieren scatter-gather). |
| **Range (ledger)** | Archivado simple. `DROP PARTITION` para datos viejos. | Hotspots. Toda escritura del día va a una partición activa. |

**Decisión:** Hash para `ACCOUNT`, Range para `LEDGER_ENTRY` ✅

---

**Documentos Relacionados:**
- [01-architecture-high-level.md](./01-architecture-high-level.md) → omponentes, patrones, TTL alineado (5s)
- [02-persistence-design.md](./02-persistence-design.md) → Modelo de datos, particionamiento
- [03-interbank-transfer-flow.md](./03-interbank-transfer-flow.md) → Flujo Saga detallado
- [05-deployment-security-observability.md](./05-deployment-security-observability.md) → CI/CD, seguridad