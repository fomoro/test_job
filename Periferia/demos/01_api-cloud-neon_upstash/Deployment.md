# 📦 DEPLOYMENT.md - POC CCS Central de Señales

## 🎯 Objetivo del POC
Validar que la arquitectura propuesta puede procesar **500 señales/segundo durante 2 minutos** manteniendo **SLA < 2 segundos** por señal, incluyendo cache con Redis y persistencia en PostgreSQL.

---

## 🚀 Configuración Rápida

### 1. 📁 Estructura del POC
```
demo/
├── .env                   # Variables de entorno
├── main.py                # API FastAPI (NO MODIFICAR)
└── requirements.txt       # Dependencias
```

### 2. 🔑 Configurar Variables de Entorno
Editar `demo/.env` con tus credenciales:

```ini
# PostgreSQL (NeonDB)
DATABASE_URL="postgresql://usuario:contraseña@servidor.neon.tech/basedatos?sslmode=require"

# Redis (Upstash) - Formato TCP
REDIS_URL="rediss://default:contraseña@instancia.upstash.io:6379"
```

### 3. 📦 Instalar Dependencias
```bash
# Navegar a la carpeta demo
cd demo

# Instalar paquetes Python
pip install -r requirements.txt
```

### 4. 🗄️ Configurar Base de Datos
Ejecutar en orden desde `scripts/database/`:

```bash
# 1. Esquema completo
psql [DATABASE_URL] -f ../scripts/database/01_schema_complete.sql

# 2. Datos maestros (vehículos, reglas)
psql [DATABASE_URL] -f ../scripts/database/02_seed_master_data.sql

# 3. Señales de prueba (opcional)
psql [DATABASE_URL] -f ../scripts/database/03_seed_signals.sql
```

---

## ▶️ Ejecutar la API

### Opción A: Desarrollo (con recarga automática)
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Opción B: Producción
```bash
python main.py
```

**Verificar que está funcionando:**
```bash
curl http://localhost:8000/health
```
✅ Respuesta esperada: `{"status":"healthy","services":{...}}`

---

## 📡 Endpoints Disponibles

### 1. ✅ Health Check
```bash
GET /health
```
Verifica conexión con PostgreSQL y Redis.

### 2. 🚨 Procesar Señal (CORE)
```bash
POST /signal
Content-Type: application/json

{
  "vehicle_id": "TRUCK-001",
  "speed": 85.5,
  "latitude": 4.7,
  "longitude": -74.1,
  "panic_button": false,
  "metadata": {}
}
```

**Respuesta:**
```json
{
  "status": "processed",
  "vehicle_id": "TRUCK-001",
  "signal_id": 12345,
  "alerts_generated": 1,
  "processing_time_ms": 245.8,
  "cache_status": "miss"
}
```

### 3. ⚙️ Actualizar Regla
```bash
POST /update-rule
Content-Type: application/json

{
  "vehicle_id": "TRUCK-001",
  "new_limit": 70
}
```

**Invalida cache** y actualiza límite de velocidad.

### 4. 📊 Estadísticas
```bash
GET /stats
```
Métricas del sistema: vehículos activos, reglas, alertas, uso de Redis.

---

## 🧪 Pruebas Rápidas

### Script Automático (`test_poc.sh`)
```bash
#!/bin/bash
API_URL="http://localhost:8000"

echo "🧪 PRUEBAS POC CCS"

echo "1. Verificar salud del sistema:"
curl -s "$API_URL/health" | jq '.status'

echo -e "\n2. Primera señal (Cache MISS):"
curl -s -X POST "$API_URL/signal" \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"TRUCK-001","speed":85,"latitude":4.7,"longitude":-74.1}' | jq '.cache_status'

echo -e "\n3. Segunda señal (Cache HIT):"
curl -s -X POST "$API_URL/signal" \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"TRUCK-001","speed":85,"latitude":4.7,"longitude":-74.1}' | jq '.cache_status'

echo -e "\n4. Actualizar regla (invalida cache):"
curl -s -X POST "$API_URL/update-rule" \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"TRUCK-001","new_limit":70}' | jq '.cache_invalidated'

echo -e "\n5. Probar botón de pánico:"
curl -s -X POST "$API_URL/signal" \
  -H "Content-Type: application/json" \
  -d '{"vehicle_id":"TAXI-101","speed":20,"panic_button":true}' | jq '.alerts_generated'

echo -e "\n✅ PRUEBAS COMPLETADAS"
```

**Ejecutar:**
```bash
chmod +x test_poc.sh
./test_poc.sh
```

### Pruebas Manuales
```bash
# Ver estadísticas
curl http://localhost:8000/stats | jq

# Probar múltiples vehículos
for i in {1..5}; do
  curl -X POST http://localhost:8000/signal \
    -H "Content-Type: application/json" \
    -d "{\"vehicle_id\":\"TRUCK-00$i\",\"speed\":$((60+i*5)),\"latitude\":4.7,\"longitude\":-74.1}"
  echo
done
```

---

## 🔍 Monitoreo y Verificación

### 📊 En PostgreSQL (NeonDB)
```sql
-- 1. Alertas recientes
SELECT * FROM alerts ORDER BY id DESC LIMIT 5;

-- 2. Verificar SLA (<2 segundos)
SELECT 
    a.vehicle_id,
    r.rule_type,
    EXTRACT(EPOCH FROM (a.timestamp - s.timestamp)) as processing_seconds,
    CASE WHEN EXTRACT(EPOCH FROM (a.timestamp - s.timestamp)) < 2 
         THEN '✅ CUMPLE SLA' ELSE '❌ VIOLA SLA' END as sla_status
FROM alerts a
LEFT JOIN signals s ON a.signal_id = s.id
LEFT JOIN rules r ON a.rule_id = r.id
ORDER BY a.id DESC LIMIT 10;

-- 3. Métricas generales
SELECT COUNT(*) as total_señales FROM signals;
SELECT COUNT(*) as total_alertas FROM alerts;
SELECT COUNT(DISTINCT vehicle_id) as vehiculos_activos FROM alerts;
```

### ⚡ En Redis (Upstash)
```bash
# Verificar conexión (desde Python)
python -c "import redis; r=redis.from_url('$REDIS_URL'); print(r.ping())"

# Ver claves existentes
python -c "import redis; r=redis.from_url('$REDIS_URL'); print(r.keys('*'))"
```

### 📈 Métricas Clave a Validar

| Métrica | Verificación | Valor Esperado |
|---------|--------------|----------------|
| **Tiempo procesamiento** | `processing_time_ms` en respuesta | < 2000 ms |
| **Cache hit rate** | `cache_status` alterna | miss → hit |
| **Alertas persistentes** | Consulta SQL a `alerts` | > 0 registros |
| **Relación señal→alerta** | `signal_id` no nulo en `alerts` | 100% de cobertura |
| **Disponibilidad servicios** | `/health` endpoint | "healthy" |

---

## 🚀 Pruebas de Carga (Performance)

### Usar scripts de `performance/`:
```bash
# Generar carga masiva (500 señales/seg x 2 min)
cd ../performance
python generar_carga.py --rate 500 --duration 120

# Monitorear métricas en tiempo real
python monitor_metrics.py

# Probar escenario de emergencia
python test_emergencia.py --vehicles 100
```

### Verificar resultados:
1. **SLA mantenido**: < 2 segundos en percentil 95 (p95)
2. **Throughput sostenido**: 500 señales/segundo
3. **Sin pérdida de datos**: Todas las señales persisten
4. **Cache efectivo**: Hit rate > 80% después de warm-up

---

## 📁 Estructura del Código (main.py)

### 🔄 Flujo Principal:
```
Señal → Validación → Cache (Redis) → PostgreSQL → Evaluar Reglas → Alertas
```

### 🏗️ Componentes:
- **FastAPI**: Servidor web async
- **asyncpg**: Conexión PostgreSQL async
- **redis-py**: Cliente Redis async
- **pydantic**: Validación de datos

### ⚡ Optimizaciones:
- **Connection pooling** para PostgreSQL
- **Cache TTL** de 5 minutos en Redis
- **Inserción batch** de señales
- **Logging estructurado**

---

## 📝 Notas Importantes

### ⚠️ Limitaciones del POC:
1. **Código monolítico**: Todo en `main.py` para simplicidad
2. **Reglas básicas**: Solo MAX_SPEED y PANIC_BUTTON
3. **Sin autenticación**: Para pruebas locales
4. **Persistencia simple**: Alertas en tabla única

### 🔄 Siguientes Pasos (si el POC es exitoso):
1. Refactorizar a Clean Architecture (`app/` domain, application, infrastructure)
2. Implementar colas de mensajería (RabbitMQ/Kafka)
3. Agregar autenticación/autorización
4. Sistema de notificaciones (email, SMS, push)
5. Dashboard de monitoreo en tiempo real

---

## 📊 Criterios de Éxito

| Criterio | Métrica | Objetivo |
|----------|---------|----------|
| **Rendimiento** | Tiempo procesamiento p95 | < 2000 ms |
| **Escalabilidad** | Throughput sostenido | 500 señales/segundo |
| **Fiabilidad** | Disponibilidad servicios | 99.9% durante prueba |
| **Consistencia** | Alertas con signal_id | 100% |
| **Cache eficiente** | Hit rate después warm-up | > 80% |

---

## 🆘 Soporte

### Documentación Adicional:
- `docs/demo/POC_OBJECTIVES.md` → Objetivos y contexto
- `docs/database/SCHEMA_DESIGN.md` → Diseño de base de datos
- `docs/INDEX.md` → Documentación general del proyecto

### Problemas Comunes:
1. **Timeout en NeonDB**: Aumentar `connect_timeout` en DATABASE_URL
2. **Redis lento**: Upstash tier gratuito tiene límites
3. **Logs excesivos**: Modificar `logging.basicConfig(level=logging.WARNING)`

---

**✅ POC Listo para Ejecutar** - Sigue los pasos en **🚀 Configuración Rápida** para comenzar.