# ==========================================
# 19_fix_properties.ps1
# CORRECCIÓN DE RUTAS (Eliminar context-path redundante)
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Corrigiendo application.properties en: $basePath" -ForegroundColor Cyan

$appProps = @'
spring.application.name=tumipay-payin-service
server.port=8080
# CORRECCION: Comentamos el context-path para evitar la ruta doble /api/api/...
# server.servlet.context-path=/api

# --- DATABASE CONFIG (NeonDB) ---
spring.datasource.url=jdbc:postgresql://ep-weathered-dawn-ae1flers-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
spring.datasource.username=neondb_owner
spring.datasource.password=npg_JFvV9G0LpxsS
spring.datasource.driver-class-name=org.postgresql.Driver

# --- HIKARI POOL ---
spring.datasource.hikari.maximum-pool-size=10
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.data-source-properties.ssl=true
spring.datasource.hikari.data-source-properties.sslfactory=org.postgresql.ssl.NonValidatingFactory

# --- JPA / HIBERNATE ---
spring.jpa.hibernate.ddl-auto=validate
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true
spring.jpa.properties.hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect

# --- LOGGING ---
logging.level.com.tumi.payln=DEBUG
logging.level.org.springframework.web=INFO
logging.level.org.hibernate.SQL=DEBUG

spring.mvc.throw-exception-if-no-handler-found=true
spring.web.resources.add-mappings=false
'@

$fullPath = Join-Path -Path $basePath -ChildPath "src\main\resources\application.properties"
$appProps | Out-File -FilePath $fullPath -Encoding UTF8 -Force

Write-Host "✅ application.properties corregido." -ForegroundColor Green
Write-Host "1. Detén el servidor (Ctrl+C)" -ForegroundColor Gray
Write-Host "2. Ejecuta: mvn spring-boot:run" -ForegroundColor White