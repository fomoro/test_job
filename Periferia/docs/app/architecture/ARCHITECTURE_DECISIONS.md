# Decisiones de Arquitectura CCS (ADR)

## ADR-001: Uso de Redis Streams para Procesamiento de Señales

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Necesidad de procesar 500 señales por segundo con garantías de entrega y priorización de emergencias.

**Decisión**: Usar Redis Streams en lugar de Kafka o RabbitMQ.

**Consecuencias**:
- ✅ **Simplicidad operativa**: Menos componentes que mantener vs Kafka
- ✅ **Performance**: Latencia sub-milisegundo para operaciones
- ✅ **Integración Python**: Soporte nativo con `redis-py`
- ✅ **Streams separados**: Facilita priorización emergencia/normal
- ❌ **Menos features enterprise**: Vs Kafka (exactly-once, replay)
- ❌ **Escalabilidad vertical**: Redis Cluster necesario > 20k RPS

**Alternativas consideradas**:
1. **Apache Kafka**: Demasiado complejo para requisitos actuales
2. **RabbitMQ**: Menor performance para streams de datos
3. **AWS Kinesis**: Lock-in cloud, mayor costo

## ADR-002: Separación de Streams para Emergencias

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Emergencias deben procesarse en <2s, señales normales pueden tolerar mayor latencia.

**Decisión**: Dos streams Redis separados: normal y emergencia.

**Consecuencias**:
- ✅ **Priorización garantizada**: Emergencias no esperan detrás de señales normales
- ✅ **Workers especializados**: Configuración y escalado independiente
- ✅ **Métricas separadas**: Monitoreo específico por tipo
- ❌ **Duplicación de lógica**: Mismos workers con diferente configuración
- ❌ **Complejidad operativa**: Dos sistemas a monitorear

## ADR-003: Particionamiento de PostgreSQL por Fecha

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Tabla `signals` crece 43M registros/día (500 RPS × 86,400s).

**Decisión**: Particionar tabla `signals` por rango mensual.

**Consecuencias**:
- ✅ **Performance queries recientes**: Índices más pequeños
- ✅ **Retención flexible**: Eliminar particiones antiguas fácilmente
- ✅ **Backup/restore granular**: Por partición
- ❌ **Consultas históricas**: Requieren UNION o consulta múltiples particiones
- ❌ **Mantenimiento**: Particiones nuevas mensuales

## ADR-004: Cache de Reglas en Redis

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Reglas consultadas en cada señal (500 veces/segundo).

**Decisión**: Cache con TTL 300 segundos en Redis.

**Consecuencias**:
- ✅ **Reducción carga DB**: 90%+ cache hit rate esperado
- ✅ **Latencia predecible**: <1ms vs 10-50ms en PostgreSQL
- ✅ **Invalidación automática**: Por TTL, no manual
- ❌ **Consistencia eventual**: Máximo 5 minutos de desfase
- ❌ **Memoria Redis**: ~100MB para 10k reglas

## ADR-005: Fast Path para Emergencias

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: SLA de <2s para botón de pánico.

**Decisión**: Pipeline optimizado solo para PANIC_BUTTON.

**Consecuencias**:
- ✅ **SLA garantizado**: Procesamiento <1500ms
- ✅ **Simplificación**: Solo reglas críticas evaluadas
- ✅ **Resiliencia**: Fallbacks definidos para cada componente
- ❌ **Dualidad de código**: Dos pipelines diferentes
- ❌ **Testing complejo**: Validar ambos caminos

## ADR-006: Async/Await vs Threads/Processes

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Alto I/O con Redis, PostgreSQL y HTTP.

**Decisión**: Usar asyncio con FastAPI.

**Consecuencias**:
- ✅ **Alta concurrencia**: Miles de conexiones simultáneas
- ✅ **Menos overhead**: vs threading/processes
- ✅ **Código legible**: `async/await` vs callbacks
- ❌ **Curva aprendizaje**: Programación asíncrona
- ❌ **Librerías blocking**: Requieren threads separados

## ADR-007: Monolithic vs Microservices

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Sistema inicial con 9,500 vehículos, crecimiento 20% anual.

**Decisión**: Arquitectura monolítica modular (no microservicios).

**Consecuencias**:
- ✅ **Simplicidad operativa**: Un solo servicio para desplegar
- ✅ **Debugging más fácil**: Trazas completas en un proceso
- ✅ **Performance**: No overhead de comunicación entre servicios
- ❌ **Acoplamiento**: Cambios afectan todo el sistema
- ❌ **Escalabilidad limitada**: No escalar componentes individualmente

## ADR-008: Health Checks y Circuit Breakers

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Sistema debe ser resiliente a fallos de dependencias.

**Decisión**: Implementar health checks y circuit breakers.

**Consecuencias**:
- ✅ **Degradación elegante**: Fallos aislados no colapsan sistema
- ✅ **Auto-recuperación**: Circuit breakers se reabren automáticamente
- ✅ **Monitoring**: Health endpoint para load balancers
- ❌ **Complejidad**: Lógica adicional a mantener
- ❌ **Falsos positivos**: Configuración sensible requerida

## ADR-009: Base de Datos Relacional vs NoSQL

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Datos estructurados con relaciones complejas (vehículos, reglas, alertas).

**Decisión**: PostgreSQL como base de datos principal.

**Consecuencias**:
- ✅ **ACID garantizado**: Transacciones para consistencia
- ✅ **SQL maduro**: Queries complejas, joins, índices
- ✅ **JSONB**: Flexibilidad donde se necesita
- ❌ **Escalabilidad horizontal**: Más compleja que NoSQL
- ❌ **Schemas rígidos**: Migraciones necesarias para cambios

## ADR-010: Cache-Aside vs Write-Through

**Fecha**: Enero 2024  
**Estado**: Aceptado  
**Contexto**: Patrón de acceso lectura-intensivo (reglas, geocercas).

**Decisión**: Cache-Aside (Lazy Loading) con TTL.

**Consecuencias**:
- ✅ **Simplicidad**: Fácil de implementar y entender
- ✅ **Eficiente**: Solo cachea lo que se usa
- ✅ **Resiliente**: Cache puede caerse sin afectar sistema
- ❌ **Cache Miss penalty**: Primera consulta más lenta
- ❌ **Consistencia eventual**: TTL necesario para invalidación

---

**Archivo:** `docs/architecture/ARCHITECTURE_DECISIONS.md`  
**Versión:** 1.0  
**Responsable:** Comité de Arquitectura CCS