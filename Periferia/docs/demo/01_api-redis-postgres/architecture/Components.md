```
📁 docs/architecture/
└── 📄 COMPONENTS.md          # 📐 Diagrama de Componentes CCS
```

---

# 🏗️ COMPONENTES DE ARQUITECTURA - CCS CENTRAL

## 📊 **DIAGRAMA DE COMPONENTES**

```mermaid
graph TB
    %% ========== CAPA DE PRESENTACIÓN ==========
    subgraph "📱 CAPA DE PRESENTACIÓN (Interfaces)"
        A1[API Gateway<br/>FastAPI] --> A2[Controladores<br/>/signal, /health]
        A3[Documentación<br/>OpenAPI 3.0] --> A1
    end
    
    %% ========== CAPA DE APLICACIÓN ==========
    subgraph "⚙️ CAPA DE APLICACIÓN (Lógica de Negocio)"
        B1[Procesador de Señales] --> B2[Evaluador de Reglas]
        B2 --> B3[Generador de Alertas]
        B4[Cache Manager<br/>Redis Client] --> B1
    end
    
    %% ========== CAPA DE INFRAESTRUCTURA ==========
    subgraph "🗄️ CAPA DE INFRAESTRUCTURA (Persistencia)"
        C1[(PostgreSQL<br/>Particionado)] --> C2[Repositorio de Señales]
        C1 --> C3[Repositorio de Reglas]
        C1 --> C4[Repositorio de Alertas]
        
        C5[(Redis Cache<br/>Upstash)] --> C6[Cache de Reglas]
        
        C7[External Services] --> C8[Notificador SMS/Email]
        C8 --> C9[API Policía]
    end
    
    %% ========== FLUJO DE DATOS ==========
    A2 -->|1. Recibe señal| B1
    B1 -->|2. Obtiene reglas| B4
    B4 -->|Cache Hit| C6
    B4 -->|Cache Miss| C3
    B1 -->|3. Persiste señal| C2
    B2 -->|4. Evalúa violaciones| B3
    B3 -->|5. Genera alerta| C4
    B3 -->|6. Notifica| C8
    
    %% ========== EXTERNOS ==========
    D1[🚛 Vehículos CCS<br/>9,000+ dispositivos] -->|Señales GPS| A1
    C9 -->|Emergencias| D2[👮 Autoridades<br/>Policía, Bomberos]
    C8 -->|Alertas| D3[📱 Propietarios<br/>App móvil]
```

---

## 🔧 **DESCRIPCIÓN DE COMPONENTES**

### **📱 CAPA DE PRESENTACIÓN**

| Componente | Tecnología | Responsabilidad |
|------------|------------|-----------------|
| **API Gateway** | FastAPI + Uvicorn | Punto único de entrada, routing, rate limiting |
| **Controladores** | FastAPI Endpoints | Validación entrada, orquestación flujo |
| **Documentación** | OpenAPI 3.0 + Swagger | Documentación automática, testing interactivo |

**Endpoints críticos:**
- `POST /signal` - Procesamiento principal de señales
- `GET /health` - Health check servicios
- `POST /update-rule` - Actualización reglas en caliente
- `GET /stats` - Métricas del sistema

### **⚙️ CAPA DE APLICACIÓN**

| Componente | Patrón | Responsabilidad |
|------------|--------|-----------------|
| **Procesador de Señales** | Command Handler | Orquestar flujo completo: validar → persistir → evaluar |
| **Evaluador de Reglas** | Business Rules Engine | Aplicar reglas de negocio (velocidad, pánico, geofence) |
| **Generador de Alertas** | Observer Pattern | Crear alertas basadas en violaciones, determinar acciones |
| **Cache Manager** | Cache-Aside Pattern | Gestionar cache Redis, invalidación, circuit breaker |

**Tipos de Reglas Implementadas:**
- `MAX_SPEED` - Exceso velocidad por vehículo
- `PANIC_BUTTON` - Botón de emergencia activado
- `UNSCHEDULED_STOP` - Detención no programada (futuro)
- `GEOFENCE_VIOLATION` - Salida zona autorizada (futuro)

### **🗄️ CAPA DE INFRAESTRUCTURA**

| Componente | Tecnología | Optimización |
|------------|------------|--------------|
| **PostgreSQL** | NeonDB (Serverless) | Tabla `signals` particionada por tiempo |
| **Redis Cache** | Upstash (Redis Cloud) | TTL 5 min, circuit breaker automático |
| **Repositorio Señales** | asyncpg + Connection Pool | Bulk inserts, 100 conexiones máx |
| **Repositorio Reglas** | Optimizado para cache | Índice `idx_rules_vehicle_active` |
| **Notificador** | Integración futura | Webhooks, SMS, Email, Push |

**Estrategia de Persistencia:**
```
Señal → PostgreSQL (tabla particionada signals)
       ↘ Evaluación → Si violación → PostgreSQL (tabla alerts)
                     ↘ Cache Redis (reglas activas)
```

---

## 🔄 **FLUJO DE UNA SEÑAL (SECUENCIA DETALLADA)**

### **1. Recepción y Validación**
```mermaid
sequenceDiagram
    participant V as Vehículo
    participant A as API Gateway
    participant C as Controlador
    participant V as Validador
    
    V->>A: POST /signal (JSON)
    A->>C: Routing
    C->>V: Validación Pydantic
    V-->>C: ✅ Datos válidos
    C->>C: timestamp = datetime.now()
```

### **2. Procesamiento Paralelo Optimizado**
```mermaid
sequenceDiagram
    participant C as Controlador
    participant R as Redis Cache
    participant P as PostgreSQL
    participant E as Evaluador
    
    par Cache y Persistencia
        C->>R: GET rules:{vehicle_id}
        C->>P: INSERT INTO signals...
    end
    
    alt Cache HIT (< 500ms)
        R-->>C: Reglas JSON
    else Cache MISS
        R-->>C: NULL
        C->>P: SELECT rules WHERE vehicle_id...
        P-->>C: Reglas DB
        C->>R: SETEX rules:{vehicle_id} 300s
    end
    
    C->>E: Evaluar reglas vs señal
```

### **3. Generación y Notificación de Alertas**
```mermaid
sequenceDiagram
    participant E as Evaluador
    participant P as PostgreSQL
    participant N as Notificador
    participant Ext as Servicios Externos
    
    E->>E: ¿Violación de regla?
    
    alt MAX_SPEED violado
        E->>P: INSERT alert (speeding)
        E->>N: Notificar propietario
    else PANIC_BUTTON activado
        E->>P: INSERT alert (emergency)
        E->>N: Notificar autoridades
        N->>Ext: API Policía (POST)
    end
    
    P-->>E: ✅ Alerta persistida
    E-->>C: Respuesta con métricas
```

---

## ⚡ **OPTIMIZACIONES DE RENDIMIENTO**

### **Nivel de Base de Datos:**
| Técnica | Implementación | Impacto |
|---------|----------------|---------|
| **Particionamiento** | Tabla `signals` por mes | Reducción 10x en tiempo query |
| **Índices optimizados** | `(vehicle_id, timestamp DESC)` | Búsqueda señales recientes O(1) |
| **Connection Pool** | asyncpg pool (100 conexiones) | Soporta 500 RPS concurrentes |
| **Bulk Operations** | `executemany()` para alertas múltiples | Reduce I/O 90% |

### **Nivel de Cache:**
| Técnica | Implementación | Impacto |
|---------|----------------|---------|
| **Cache-Aside** | Redis + TTL 300s | Latencia: 500ms → 5ms |
| **Circuit Breaker** | Deshabilitar Redis si falla | Disponibilidad 99.9% |
| **Invalidación activa** | DELETE en `/update-rule` | Consistencia inmediata |
| **Serialización eficiente** | JSON (vs pickle) | Tamaño reducido 60% |

### **Nivel de Aplicación:**
| Técnica | Implementación | Impacto |
|---------|----------------|---------|
| **Async/Await** | FastAPI + asyncpg + redis.asyncio | Concurrencia masiva |
| **Timeouts agresivos** | Redis: 500ms, PG: 1500ms | Fallar rápido vs. violar SLA |
| **Logging estructurado** | Nivel WARNING en producción | Reducción I/O logs 80% |
| **Health checks ligeros** | Solo conexiones esenciales | Monitoreo sin overhead |

---

## 📈 **ESCALABILIDAD HORIZONTAL**

### **Escenario Actual (POC Validado):**
```
1 Instancia FastAPI → 500 RPS → PostgreSQL + Redis Cloud
```

### **Escenario de Producción (Recomendado):**
```
Load Balancer
    ├── Instancia API 1 (500 RPS)
    ├── Instancia API 2 (500 RPS)
    ├── Instancia API N (500 RPS)
    │
    ├── Redis Cluster (3 nodos)
    └── PostgreSQL Read Replicas (2)
        └── PostgreSQL Primary
```

### **Límites de Escala Identificados:**
| Componente | Límite Actual | Límite con Optimización |
|------------|---------------|-------------------------|
| **FastAPI** | ~500 RPS/instancia | ~2000 RPS con Gunicorn workers |
| **PostgreSQL** | ~1000 INSERTs/seg | ~5000 INSERTs/seg con batching |
| **Redis** | ~10,000 ops/seg | ~100,000 ops/seg con cluster |
| **Network** | Latencia 200-500ms (cloud) | <50ms (on-premise) |

---

## 🛡️ **PATRONES DE DISEÑO APLICADOS**

### **Patrones Estructurales:**
| Patrón | Aplicación | Beneficio |
|--------|------------|-----------|
| **Layered Architecture** | Presentación → Aplicación → Infraestructura | Separación responsabilidades |
| **Repository Pattern** | `VehicleRepository`, `AlertRepository` | Abstrac