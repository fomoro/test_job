
# 🐳 Guía Local: Docker Compose para CCS

## 📋 Configuración Local Únicamente

### ✅ Estructura del Proyecto
```
periferia-project-ccs/
├── docker/
│   └── docker-compose.yml    # <-- Este archivo
├── scripts/
│   └── database/
│       ├── 01_schema_complete.sql
│       └── 02_seed_master_data.sql
└── (otros directorios)
```

---

## 🚀 Configuración en 3 Pasos

### Paso 1: Archivo `docker-compose.yml`

**Ubicación:** `periferia-project-ccs/docker/docker-compose.yml`

```yaml
version: '3.8'

services:
  # 1. Base de Datos PostgreSQL
  db:
    image: postgres:15-alpine
    container_name: ccs_postgres_local
    restart: always
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password123
      POSTGRES_DB: ccs_db
    ports:
      - "5433:5432"  # Puerto 5433 para Windows
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ../scripts/database:/docker-entrypoint-initdb.d  # Scripts SQL automáticos

  # 2. Redis Cache
  redis:
    image: redis:alpine
    container_name: ccs_redis_local
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

volumes:
  pgdata:
  redisdata:
```

---

### Paso 2: Inicialización

1. **Ubicarse en la carpeta:**
```powershell
cd periferia-project-ccs/docker
```

2. **Limpiar contenedores anteriores (OBLIGATORIO):**
```powershell
docker-compose down -v
```

3. **Iniciar servicios:**
```powershell
docker-compose up -d
```

4. **Verificar estado:**
```powershell
docker-compose ps
```
✅ Deberías ver:
```
NAME                 STATUS              PORTS
ccs_postgres_local   Up 2 minutes        0.0.0.0:5433->5432/tcp
ccs_redis_local      Up 2 minutes        0.0.0.0:6379->6379/tcp
```

---

### Paso 3: Verificación

#### **A) Verificar PostgreSQL (pgAdmin):**
- **Servidor:** `localhost`
- **Puerto:** `5433`
- **Usuario:** `admin`
- **Contraseña:** `password123`
- **Base de datos:** `ccs_db`

**Consulta de verificación:**
```sql
-- Ejecutar en pgAdmin
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

#### **B) Verificar Redis:**
```powershell
# Acceder al contenedor
docker exec -it ccs_redis_local redis-cli ping
```
✅ Respuesta: `PONG`

---

## 🗄️ Qué Hace Docker Compose

| Servicio | Puerto | Propósito | Acceso |
|----------|--------|-----------|--------|
| PostgreSQL | 5433 | Base de datos principal | pgAdmin: localhost:5433 |
| Redis | 6379 | Cache para reglas | redis-cli o cliente Redis |

### 📁 Scripts SQL Automáticos
Los archivos en `scripts/database/` se ejecutan en **orden alfabético** al iniciar PostgreSQL:

1. `01_schema_complete.sql` → Crea todas las tablas
2. `02_seed_master_data.sql` → Inserta datos iniciales

**NOTA:** Solo se ejecutan la primera vez (cuando el volumen `pgdata` está vacío).

---

## 🔧 Comandos Útiles

| Comando | Descripción |
|---------|-------------|
| `docker-compose up -d` | Iniciar servicios en background |
| `docker-compose down` | Detener servicios |
| `docker-compose down -v` | Detener y ELIMINAR volúmenes |
| `docker-compose logs` | Ver logs |
| `docker-compose logs -f db` | Seguir logs de PostgreSQL |
| `docker-compose ps` | Ver estado de contenedores |

---

## ✅ Verificación Final

1. **PostgreSQL funcionando:**
```powershell
# Desde PowerShell
Test-NetConnection localhost -Port 5433
```

2. **Redis funcionando:**
```powershell
docker exec ccs_redis_local redis-cli info | findstr "uptime"
```

3. **Tablas creadas:**
```sql
-- En pgAdmin, conectar a localhost:5433
-- Ejecutar:
SELECT COUNT(*) as tablas_creadas 
FROM information_schema.tables 
WHERE table_schema = 'public';
```

---

**🎯 Listo.** Con esta configuración tienes:
- ✅ PostgreSQL local en puerto 5433
- ✅ Redis local en puerto 6379
- ✅ Scripts SQL ejecutados automáticamente
- ✅ Todo listo para desarrollo local

¿Necesitas algo más específico para la configuración local?