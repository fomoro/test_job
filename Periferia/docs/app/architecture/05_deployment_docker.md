# Diagrama de Despliegue - Docker Compose

## Contexto
Configuración de entorno de desarrollo y producción para el sistema CCS utilizando Docker Compose, permitiendo despliegue consistente en cualquier entorno.

## Diagrama de Despliegue

```mermaid
graph TB
    subgraph "Host / Servidor Local"
        subgraph "Docker Compose Stack - CCS"
            subgraph "Red Interna Docker: ccs-network"
                APP[CCS API Container<br/>FastAPI + Python 3.11<br/>Puerto: 8000:8000]
                
                PG[(PostgreSQL 15<br/>Puerto interno: 5432<br/>Puerto mapeado: 5433]
                
                RD[(Redis 7.2<br/>Streams + Cache<br/>Puerto: 6379:6379]
                
                MON[Monitor Container<br/>monitor_metrics.py<br/>Dashboard en tiempo real]
                
                TEST[Test Container<br/>Opcional - Solo pruebas]
            end
            
            VOL1[Volume: ccs-pgdata<br/>/var/lib/postgresql/data]
            VOL2[Volume: ccs-redisdata<br/>/data]
            VOL3[Volume: ccs-scripts<br/>/docker-entrypoint-initdb.d]
            
            SCRIPT[Scripts SQL<br/>01_schema_complete.sql<br/>02_seed_master_data.sql<br/>03_seed_signals.sql]
        end
        
        DOCKERFILE[Dockerfile<br/>Python 3.11-slim<br/>Requirements.txt]
        COMPOSE[docker-compose.yml<br/>Version: 3.8]
        ENV[Archivo .env<br/>Variables de entorno]
    end
    
    subgraph "Red Externa - Clientes"
        V[Vehículos/Sensores<br/>HTTP POST:8000/signal]
        OWN[Propietarios App<br/>HTTP GET:8000/rules<br/>HTTP POST:8000/geofence]
        ADMIN[Central CCS Web<br/>HTTP:8000/docs<br/>HTTP:8000/metrics]
        TESTER[Load Tester<br/>generar_carga.py<br/>test_emergencia.py]
    end
    
    subgraph "Servicios Cloud - Opcional (Producción)"
        AWS[AWS RDS PostgreSQL<br/>db.t3.large<br/>Multi-AZ]
        AZURE[Azure Cache for Redis<br/>Premium P1<br/>Replicación]
        LB[Load Balancer Cloud<br/>AWS ALB / Azure LB<br/>SSL Termination]
        ECR[Container Registry<br/>ECR / ACR<br/>Imágenes Docker]
    end
    
    %% Conexiones Locales
    VOL1 --> PG
    VOL2 --> RD
    VOL3 --> PG
    SCRIPT --> VOL3
    
    APP --> PG
    APP --> RD
    MON --> APP
    TEST -.->|Pruebas de carga| APP
    
    DOCKERFILE --> APP
    COMPOSE --> APP
    COMPOSE --> PG
    COMPOSE --> RD
    ENV --> APP
    ENV --> PG
    
    %% Conexiones Clientes
    V --> APP
    OWN --> APP
    ADMIN --> APP
    TESTER -.-> APP
    
    %% Conexiones Cloud (opcionales)
    APP -.->|Migración producción| AWS
    RD -.->|Escalabilidad| AZURE
    APP -.->|High Availability| LB
    APP -.->|CI/CD Pipeline| ECR
    
    %% Estilos
    style APP fill:#cce5ff
    style PG fill:#ffebcc
    style RD fill:#ffcccc
    style MON fill:#ccffcc
    style AWS fill:#f0f0f0
    style AZURE fill:#f0f0f0
```

## Archivos de Configuración

### 1. `docker-compose.yml` (Completo)
```yaml
version: '3.8'

name: ccs-central-system

services:
  # 1. Base de Datos PostgreSQL
  postgres:
    image: postgres:15-alpine
    container_name: ccs-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-admin}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password123}
      POSTGRES_DB: ${POSTGRES_DB:-ccs_db}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "${POSTGRES_PORT:-5433}:5432"
    volumes:
      - ccs-pgdata:/var/lib/postgresql/data
      - ./scripts/database:/docker-entrypoint-initdb.d:ro
      - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro
    command: >
      postgres -c config_file=/etc/postgresql/postgresql.conf
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-admin}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - ccs-network

  # 2. Redis para Streams y Cache
  redis:
    image: redis:7.2-alpine
    container_name: ccs-redis
    restart: unless-stopped
    command: >
      redis-server 
      --appendonly yes 
      --appendfsync everysec 
      --maxmemory 512mb 
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
    ports:
      - "${REDIS_PORT:-6379}:6379"
    volumes:
      - ccs-redisdata:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf:ro
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - ccs-network

  # 3. API CCS Principal
  api:
    build:
      context: ../app
      dockerfile: Dockerfile
      args:
        PYTHON_VERSION: 3.11-slim
    container_name: ccs-api
    restart: unless-stopped
    environment:
      DATABASE_URL: "postgresql://${POSTGRES_USER:-admin}:${POSTGRES_PASSWORD:-password123}@postgres:5432/${POSTGRES_DB:-ccs_db}"
      REDIS_URL: "redis://redis:6379"
      REDIS_STREAM_NAME: "ccs_signals_stream"
      EMERGENCY_STREAM_NAME: "ccs_emergency_stream"
      API_HOST: "0.0.0.0"
      API_PORT: "8000"
      LOG_LEVEL: "${LOG_LEVEL:-INFO}"
      API_INSTANCE_ID: "ccs-api-${HOSTNAME}"
    ports:
      - "${API_PORT:-8000}:8000"
    volumes:
      - ../app:/app:ro
      - ccs-logs:/app/logs
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - ccs-network
    # Escalabilidad: descomentar para múltiples instancias
    # deploy:
    #   replicas: 3
    #   update_config:
    #     parallelism: 1
    #     delay: 10s

  # 4. Monitor de Métricas
  monitor:
    build:
      context: ../performance
      dockerfile: Dockerfile.monitor
    container_name: ccs-monitor
    restart: unless-stopped
    environment:
      API_URL: "http://api:8000"
      MONITOR_INTERVAL: "2"
      OUTPUT_DIR: "/reports"
    ports:
      - "${MONITOR_PORT:-8080}:8080"
    volumes:
      - ccs-reports:/reports
      - ../performance:/monitor:ro
    depends_on:
      api:
        condition: service_healthy
    networks:
      - ccs-network

  # 5. Load Tester (Opcional - Solo para pruebas)
  tester:
    build:
      context: ../performance
      dockerfile: Dockerfile.tester
    container_name: ccs-tester
    restart: "no"
    environment:
      API_URL: "http://api:8000"
      TARGET_RPS: "500"
      DURATION_SECONDS: "120"
    volumes:
      - ../performance:/tester:ro
      - ccs-test-results:/results
    depends_on:
      api:
        condition: service_healthy
    networks:
      - ccs-network
    # Ejecutar manualmente: docker-compose run tester

volumes:
  ccs-pgdata:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PGDATA_VOLUME_PATH:-./volumes/postgres}
  ccs-redisdata:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${REDIS_VOLUME_PATH:-./volumes/redis}
  ccs-logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${LOGS_VOLUME_PATH:-./volumes/logs}
  ccs-reports:
    driver: local
  ccs-test-results:
    driver: local

networks:
  ccs-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
    driver_opts:
      com.docker.network.bridge.name: ccs-bridge
```

### 2. `Dockerfile` para API CCS
```dockerfile
# Dockerfile para API CCS
FROM python:3.11-slim AS builder

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install --user -r requirements.txt

# Stage final
FROM python:3.11-slim

WORKDIR /app

# Copiar dependencias instaladas
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Crear usuario no root
RUN useradd -m -u 1000 ccsuser && \
    chown -R ccsuser:ccsuser /app
USER ccsuser

# Copiar código de la aplicación
COPY --chown=ccsuser:ccsuser . .

# Exponer puerto
EXPOSE 8000

# Comando de ejecución
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### 3. `Dockerfile.monitor` para Monitor
```dockerfile
# Dockerfile para Monitor CCS
FROM python:3.11-slim

WORKDIR /monitor

# Instalar dependencias
RUN pip install aiohttp

COPY monitor_metrics.py .
COPY requirements_monitor.txt .

RUN pip install -r requirements_monitor.txt

# Crear directorio para reportes
RUN mkdir -p /reports && chmod 777 /reports

CMD ["python", "monitor_metrics.py", "--url", "http://api:8000", "--interval", "2"]
```

### 4. `Dockerfile.tester` para Load Tester
```dockerfile
# Dockerfile para Load Tester
FROM python:3.11-slim

WORKDIR /tester

# Instalar dependencias
RUN pip install aiohttp

COPY generar_carga.py .
COPY test_emergencia.py .
COPY requirements_tester.txt .

RUN pip install -r requirements_tester.txt

# Directorio para resultados
RUN mkdir -p /results && chmod 777 /results

# Comando por defecto (se sobrescribe al ejecutar)
CMD ["python", "generar_carga.py", "--url", "http://api:8000", "--rps", "100", "--duration", "30"]
```

### 5. Archivo `.env` de configuración
```bash
# .env - Variables de entorno CCS

# PostgreSQL
POSTGRES_USER=admin
POSTGRES_PASSWORD=password123
POSTGRES_DB=ccs_db
POSTGRES_PORT=5433

# Redis
REDIS_PORT=6379

# API CCS
API_PORT=8000
LOG_LEVEL=INFO
WORKERS=4
MAX_CONCURRENCY=1000

# Monitor
MONITOR_PORT=8080
MONITOR_INTERVAL=2

# Paths de volúmenes
PGDATA_VOLUME_PATH=./volumes/postgres
REDIS_VOLUME_PATH=./volumes/redis
LOGS_VOLUME_PATH=./volumes/logs

# Configuración de performance
TARGET_RPS=500
EMERGENCY_SLA_MS=2000
CACHE_TTL_SECONDS=300

# URLs internas
DATABASE_URL=postgresql://admin:password123@postgres:5432/ccs_db
REDIS_URL=redis://redis:6379
```

## Configuraciones de Optimización

### 1. `postgresql.conf` - Optimización PostgreSQL
```conf
# postgresql.conf optimizado para CCS

# Memory
shared_buffers = 256MB
effective_cache_size = 768MB
work_mem = 4MB
maintenance_work_mem = 64MB

# Write Ahead Log
wal_level = replica
fsync = on
synchronous_commit = on
wal_buffers = 16MB
checkpoint_timeout = 10min
max_wal_size = 2GB
min_wal_size = 1GB

# Query Planning
random_page_cost = 1.1
effective_io_concurrency = 200
default_statistics_target = 100

# Connections
max_connections = 200
superuser_reserved_connections = 3

# Autovacuum
autovacuum = on
log_autovacuum_min_duration = 0
autovacuum_max_workers = 3
autovacuum_naptime = 1min
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50

# Partitioning
enable_partition_pruning = on
enable_partitionwise_join = on
enable_partitionwise_aggregate = on

# Performance
jit = off  # Mejor para cargas OLTP
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
```

### 2. `redis.conf` - Optimización Redis
```conf
# redis.conf optimizado para CCS

# General
daemonize no
protected-mode no
port 6379
tcp-backlog 511
timeout 0
tcp-keepalive 300

# Memory
maxmemory 512mb
maxmemory-policy allkeys-lru
maxmemory-samples 5

# Persistence
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Performance
hz 10
dynamic-hz yes
rdbcompression yes
rdbchecksum yes
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Streams
stream-node-max-entries 100
stream-node-max-bytes 4096
```

## Comandos de Operación

### 1. Iniciar el sistema completo
```bash
# Clonar repositorio
git clone <repo-url>
cd CCS-Periferia/docker

# Configurar variables de entorno (opcional)
cp .env.example .env

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Ver estado de todos los servicios
docker-compose ps
```

### 2. Comandos comunes de operación
```bash
# Detener todos los servicios
docker-compose down

# Detener y eliminar volúmenes (ADVERTENCIA: elimina datos)
docker-compose down -v

# Reiniciar un servicio específico
docker-compose restart api

# Ver logs de un servicio
docker-compose logs -f postgres
docker-compose logs -f redis
docker-compose logs -f api

# Escalar workers de la API
docker-compose up -d --scale api=3

# Ejecutar pruebas de carga
docker-compose run --rm tester python generar_carga.py --rps 500 --duration 120

# Ejecutar pruebas de emergencia
docker-compose run --rm tester python test_emergencia.py --concurrent 50

# Acceder a PostgreSQL
docker-compose exec postgres psql -U admin -d ccs_db

# Acceder a Redis CLI
docker-compose exec redis redis-cli

# Backup de base de datos
docker-compose exec postgres pg_dump -U admin ccs_db > backup_$(date +%Y%m%d).sql

# Restaurar base de datos
docker-compose exec -T postgres psql -U admin -d ccs_db < backup.sql
```

### 3. Script de inicialización `init.sh`
```bash
#!/bin/bash
# init.sh - Script de inicialización CCS

set -e

echo "🚀 Inicializando Sistema CCS..."

# 1. Verificar Docker y Docker Compose
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi

echo "✅ Docker y Docker Compose verificados"

# 2. Crear directorios necesarios
mkdir -p volumes/postgres volumes/redis volumes/logs
echo "✅ Directorios de volúmenes creados"

# 3. Configurar variables de entorno si no existen
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde plantilla"
    cp .env.example .env
    echo "⚠️  Por favor edita el archivo .env con tus configuraciones"
fi

# 4. Construir imágenes
echo "🔨 Construyendo imágenes Docker..."
docker-compose build

# 5. Iniciar servicios
echo "⚡ Iniciando servicios..."
docker-compose up -d

# 6. Esperar a que los servicios estén saludables
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# 7. Verificar salud
echo "🏥 Verificando salud del sistema..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Sistema CCS iniciado correctamente"
    echo "📊 Dashboard: http://localhost:8080"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo "🔧 Health: http://localhost:8000/health"
else
    echo "❌ Error: La API no responde"
    docker-compose logs api
    exit 1
fi

# 8. Cargar datos iniciales (opcional)
read -p "¿Deseas cargar datos de prueba? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "📦 Cargando datos de prueba..."
    docker-compose exec postgres psql -U admin -d ccs_db -c "SELECT COUNT(*) FROM vehicles;"
fi

echo "🎉 Sistema CCS listo para usar!"
```

## Configuración para Producción

### 1. `docker-compose.prod.yml`
```yaml
version: '3.8'

services:
  api:
    image: ccs-api:prod
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    secrets:
      - db_password
      - redis_password

  postgres:
    image: postgres:15-alpine
    deploy:
      placement:
        constraints: [node.role == manager]
      resources:
        limits:
          cpus: '2'
          memory: 4G
    volumes:
      - postgres-data:/var/lib/postgresql/data
    configs:
      - source: postgresql-prod.conf
        target: /etc/postgresql/postgresql.conf

  redis:
    image: redis:7.2-alpine
    deploy:
      replicas: 2
    command: >
      redis-server --appendonly yes
      --requirepass $$REDIS_PASSWORD

secrets:
  db_password:
    external: true
  redis_password:
    external: true

configs:
  postgresql-prod.conf:
    file: ./config/postgresql-prod.conf
  redis-prod.conf:
    file: ./config/redis-prod.conf

volumes:
  postgres-data:
    driver: local
```

### 2. Script de despliegue producción `deploy-prod.sh`
```bash
#!/bin/bash
# deploy-prod.sh - Despliegue en producción

set -e

ENVIRONMENT=${1:-staging}
REGISTRY="123456789.dkr.ecr.us-east-1.amazonaws.com"
IMAGE_TAG="ccs-api:$(git rev-parse --short HEAD)"

echo "🚀 Desplegando CCS a $ENVIRONMENT"

# 1. Login al registry
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $REGISTRY

# 2. Construir y etiquetar imagen
docker build -t $REGISTRY/ccs-api:$IMAGE_TAG -f Dockerfile.prod .
docker push $REGISTRY/ccs-api:$IMAGE_TAG

# 3. Actualizar stack Docker Swarm
docker stack deploy -c docker-compose.prod.yml ccs-$ENVIRONMENT

# 4. Verificar despliegue
sleep 30
docker service ls | grep ccs-$ENVIRONMENT

# 5. Health check
curl -f https://api-$ENVIRONMENT.ccs.com.co/health || exit 1

echo "✅ Despliegue completado: $IMAGE_TAG"
```

## Monitoreo y Logging

### 1. Configuración de Logging
```yaml
# docker-compose.logging.yml
version: '3.8'

services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "10"
        tag: "ccs-api"

  # Opcional: Agregar ELK stack para logging centralizado
  elasticsearch:
    image: elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false

  logstash:
    image: logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: kibana:8.11.0
    ports:
      - "5601:5601"
```

### 2. Dashboard de Métricas
```bash
# Acceder al dashboard del monitor
# Local: http://localhost:8080
# Producción: https://monitor.ccs.com.co

# Métricas disponibles:
# - RPS (Señales por segundo)
# - Latencia P95/P99
# - Cumplimiento SLA (<2s)
# - Health de servicios
# - Uso de recursos
# - Alertas activas
```

## Consideraciones de Seguridad

### 1. Seguridad en Docker
```bash
# Ejecutar como usuario no root
USER ccsuser

# Limitar capacidades del contenedor
cap_drop:
  - ALL
cap_add:
  - NET_BIND_SERVICE

# Configurar seccomp profile
security_opt:
  - seccomp:./seccomp-profile.json

# Read-only filesystem
read_only: true
tmpfs:
  - /tmp
```

### 2. Network Security
```yaml
networks:
  ccs-network:
    driver: bridge
    internal: false  # true para redes internas
    ipam:
      config:
        - subnet: 172.20.0.0/24
    enable_ipv6: false
```

## Troubleshooting

### Problemas Comunes y Soluciones
```bash
# 1. PostgreSQL no inicia
docker-compose logs postgres
# Verificar: permisos de volumen, puerto disponible

# 2. Redis connection refused
docker-compose exec redis redis-cli ping
# Verificar: memoria disponible, configuración

# 3. API no responde
curl http://localhost:8000/health
docker-compose logs api
# Verificar: variables de entorno, conexión a DB/Redis

# 4. Alto uso de CPU/Memoria
docker stats
# Soluciones: optimizar queries, aumentar recursos, escalar

# 5. Logs de errores
docker-compose logs --tail=100 --follow api
```

### Health Checks Integrados
```bash
# Verificar salud de todos los servicios
curl http://localhost:8000/health | jq .

# Verificar PostgreSQL
docker-compose exec postgres pg_isready -U admin

# Verificar Redis
docker-compose exec redis redis-cli ping

# Verificar métricas
curl http://localhost:8000/metrics | jq '.processing'
```

## Escalabilidad

### Escalado Horizontal
```bash
# Escalar API a 3 instancias
docker-compose up -d --scale api=3

# Escalar workers específicos
docker-compose up -d --scale worker-emergency=2 --scale worker-normal=4

# Usar Docker Swarm para producción
docker swarm init
docker stack deploy -c docker-compose.prod.yml ccs
```

### Auto-scaling (Ejemplo con métricas)
```bash
# Script de auto-scaling basado en RPS
#!/bin/bash
CURRENT_RPS=$(curl -s http://localhost:8000/metrics | jq '.processing.signals_per_second')
TARGET_RPS=500
CURRENT_INSTANCES=$(docker-compose ps api | grep -c "Up")

if (( $(echo "$CURRENT_RPS > $TARGET_RPS * 0.8" | bc -l) )); then
    NEW_INSTANCES=$((CURRENT_INSTANCES + 1))
    echo "⚡ Escalando a $NEW_INSTANCES instancias (RPS: $CURRENT_RPS)"
    docker-compose up -d --scale api=$NEW_INSTANCES
fi
```

---

**Archivo:** `docs/architecture/05_deployment_docker.md`  
**Versión:** 1.0  
**Última actualización:** Enero 2024  
**Responsable:** Equipo DevOps CCS