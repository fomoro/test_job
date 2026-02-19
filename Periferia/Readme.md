# CCS - Sistema de Seguimiento Vehicular

## 🎯 Descripción del Proyecto

Sistema de monitoreo en tiempo real para vehículos de carga, transporte público y particulares. Procesa 500+ señales por segundo con respuesta a emergencias en menos de 2 segundos.

## 📋 Requisitos del Reto Técnico

### Contexto
CCS (Compañía Colombiana de Seguimiento) monitorea:
- **1,500 camiones** (cámaras internas, temperatura de carga)
- **5,000 vehículos** (transporte público y particular)
- **3,000 motocicletas**
- Crecimiento del **20% anual** por 3 años

### Requisitos Técnicos
- ✅ **500 señales/segundo** sostenidas por 2 minutos
- ✅ **Emergencias procesadas en <2 segundos**
- ✅ Escalabilidad horizontal
- ✅ Code coverage > 50%

## 🏗️ Arquitectura del Sistema

### Componentes Principales
1. **API Gateway** - FastAPI con endpoints REST
2. **Redis Streams** - Procesamiento en tiempo real
3. **PostgreSQL** - Base de datos particionada
4. **Workers** - Procesamiento asíncrono
5. **Monitoring** - Dashboard en tiempo real

### Diagramas de Arquitectura
- [Componentes](docs/app/architecture/01_component_diagram.md)
- [Secuencia de Emergencia](docs/app/architecture/02_emergency_sequence.md)
- [Modelo Entidad-Relación](docs/app/architecture/04_entity_relationship.md)
- [Despliegue Docker](docs/app/architecture/05_deployment_docker.md)

## 🚀 Instalación Rápida

### 1. Prerrequisitos
```bash
# Docker y Docker Compose
docker --version
docker-compose --version

# Python 3.11+ (opcional para desarrollo)
python --version
```

### 2. Clonar e Iniciar
```bash
# Clonar repositorio
git clone <repository-url>
cd Periferia

# Iniciar con Docker Compose
cd docker
docker-compose up -d

# Verificar servicios
docker-compose ps
```

### 3. Acceder a los Servicios
- **API**: http://localhost:8000
- **Documentación API**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Métricas**: http://localhost:8000/metrics

## 🧪 Pruebas de Performance

### Prueba de Carga (500 RPS)
```bash
cd performance
python generar_carga.py --rps 500 --duration 120
```

### Prueba de Emergencias (<2s)
```bash
cd performance
python test_emergencia.py --concurrent 50 --workers 10
```

### Dashboard de Monitoreo
```bash
cd performance
python monitor_metrics.py --url http://localhost:8000
```

## 📁 Estructura del Proyecto

```
Periferia/
├── app/                    # Código fuente principal
│   ├── api/               # Endpoints FastAPI
│   ├── application/       # Lógica de negocio
│   ├── domain/           # Modelos y enums
│   └── infrastructure/   # Conexiones a servicios externos
├── docker/               # Configuración Docker
├── docs/                # Documentación
├── performance/         # Pruebas de carga y monitor
├── scripts/            # Scripts de BD y despliegue
└── tests/              # Pruebas unitarias e integración
```

## 🔧 Endpoints Principales

### Señales
```http
POST /signal
Content-Type: application/json

{
    "vehicle_id": "TRUCK-001",
    "speed": 65.5,
    "latitude": 4.60971,
    "longitude": -74.08175,
    "panic_button": false,
    "temperature": -15.0
}
```

### Configuración
```http
POST /geofence     # Definir geocerca
POST /schedule     # Definir horario
POST /update-rule  # Actualizar regla
```

### Monitoreo
```http
GET /health     # Estado del sistema
GET /metrics    # Métricas detalladas
```

## 🗄️ Base de Datos

### Esquema Principal
```sql
-- Tablas principales
owners          # Dueños de vehículos
vehicles        # Información vehicular
rules           # Reglas configurables
signals         # Señales (particionada por fecha)
alerts          # Alertas generadas
geofences       # Geocercas
schedules       # Horarios programados
notifications   # Histórico de notificaciones
```

### Inicializar Base de Datos
```bash
# Ejecutar scripts SQL
cd scripts/database
# 1. Esquema completo
psql -U admin -d ccs_db -f 01_schema_complete.sql
# 2. Datos maestros
psql -U admin -d ccs_db -f 02_seed_master_data.sql
# 3. Señales de prueba
psql -U admin -d ccs_db -f 03_seed_signals.sql
```

## 🧪 Testing

### Ejecutar Pruebas
```bash
# Unit tests
cd tests
pytest unit/ -v

# Integration tests
pytest integration/ -v

# Con cobertura
pytest --cov=app --cov-report=html
```

### Coverage Report
```bash
# Generar reporte
./scripts/tests/run_coverage.sh

# Ver en navegador
open htmlcov/index.html
```

## 📊 Métricas y Monitoreo

### Métricas Clave
- **RPS**: Señales por segundo (objetivo: 500)
- **Latencia Emergencia**: P95 < 2000ms
- **Cache Hit Rate**: > 90%
- **Disponibilidad**: 99.9%

### Dashboard
```bash
# Iniciar monitor
cd performance
python monitor_metrics.py

# Ver reportes en
open performance/results/*.json
```

## 🔄 Escalabilidad

### Crecimiento Proyectado
| Año | Vehículos | Señales/Día | Almacenamiento |
|-----|-----------|-------------|----------------|
| 1   | 9,500     | 43 millones | ~500 GB        |
| 2   | 11,400    | 51 millones | ~600 GB        |
| 3   | 13,680    | 62 millones | ~720 GB        |

### Estrategias de Escalado
1. **Horizontal**: Múltiples instancias de API
2. **Vertical**: PostgreSQL con réplicas de lectura
3. **Cache**: Redis Cluster para mayor throughput
4. **Particionamiento**: Tabla signals por mes

## 🐛 Troubleshooting

### Problemas Comunes

1. **PostgreSQL no inicia**
```bash
docker-compose logs postgres
# Verificar volumenes y puertos
```

2. **Redis connection refused**
```bash
docker-compose exec redis redis-cli ping
```

3. **API no responde**
```bash
curl http://localhost:8000/health
docker-compose logs api
```

4. **Alto uso de recursos**
```bash
docker stats
# Optimizar queries o escalar recursos
```

## 📚 Documentación Adicional

### Decisiones de Arquitectura
- [ADR Document](docs/app/architecture/ARCHITECTURE_DECISIONS.md)

### Flujos del Sistema
- [Flujos CCS](docs/app/database/CCS_SYSTEM_FLOWS.md)

### Performance Baseline
- [Línea Base](docs/app/database/CCS_PERFORMANCE_BASELINE.md)

## 📞 Soporte

### Comandos Útiles
```bash
# Ver todos los logs
docker-compose logs -f

# Backup de base de datos
docker-compose exec postgres pg_dump -U admin ccs_db > backup.sql

# Restaurar base de datos
docker-compose exec -T postgres psql -U admin -d ccs_db < backup.sql

# Limpiar entorno
docker-compose down -v
```

### Variables de Entorno Críticas
```bash
# En docker/.env
POSTGRES_USER=admin
POSTGRES_PASSWORD=password123
REDIS_URL=redis://redis:6379
API_PORT=8000
```

## 📄 Licencia

Este proyecto es para fines de evaluación técnica. Desarrollado para el reto técnico de CCS.

---

**Estado**: ✅ Completado  
**Última Actualización**: Enero 2024  
**Equipo**: Arquitectura CCS