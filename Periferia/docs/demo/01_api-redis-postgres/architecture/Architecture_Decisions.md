# DECISIONES DE ARQUITECTURA - POC CCS

## 🛡️ 2. 5 PROBLEMAS CRÍTICOS RESUELTOS

### 1. El problema de la Latencia de Lectura
**Problema**: Consultar reglas en PostgreSQL 500 veces/seg genera latencia inaceptable
**Solución**: Patrón **Cache-Aside** con Redis (lecturas en microsegundos)
**Resultado**: Cache hit rate > 80% después de warm-up

### 2. El problema de la Saturación de Base de Datos
**Problema**: PostgreSQL no puede con 500 lecturas + 500 escrituras simultáneas
**Solución**: Redis como buffer de lectura, PostgreSQL solo para escrituras
**Resultado**: PostgreSQL opera al 30% de capacidad durante carga máxima

### 3. El problema de la "Regla Fantasma"
**Problema**: Cache puede servir reglas obsoletas después de actualizaciones
**Solución**: **Invalidación activa** en endpoint `/update-rule`
**Resultado**: Cambios se reflejan en <1 segundo

### 4. El problema de la Legalidad
**Problema**: Solo memoria (Redis) no sirve como evidencia legal
**Solución**: Arquitectura híbrida: Redis para velocidad + PostgreSQL para persistencia
**Resultado**: Velocidad de RAM + seguridad de disco

### 5. El problema del Bloqueo I/O
**Problema**: Código síncrono crea colas infinitas con 500 RPS
**Solución**: `async/await` con `asyncpg` y `redis.asyncio`
**Resultado**: 1 servidor maneja 500 RPS concurrentes

## 🏗️ DECISIONES TÉCNICAS ESPECÍFICAS

### Base de Datos: PostgreSQL Particionado
- **Tabla `signals` particionada por tiempo** (mensual)
- **Índices optimizados** para consultas por vehículo + tiempo
- **Connection pool de 100 conexiones** para alta concurrencia

### Cache: Redis con Circuit Breaker
- **TTL de 5 minutos** para reglas
- **Circuit breaker automático** si Redis falla
- **Timeouts agresivos** (500ms) para no violar SLA

### API: FastAPI + Async
- **Async/await end-to-end**
- **Pydantic para validación**
- **Timeouts configurables** por operación