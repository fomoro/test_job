# ==========================================
# CONFIGURACIÓN DE ARCHIVOS BASE
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Escribiendo configuraciones en: $basePath" -ForegroundColor Cyan

# Función para escribir contenido desde archivo
function Write-FileFromTemplate {
    param (
        [string]$relativePath, 
        [string]$templateContent
    )
    $fullPath = Join-Path -Path $basePath -ChildPath $relativePath
    
    # Asegurar que el directorio existe
    $parentDir = Split-Path -Parent $fullPath
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
    }

    # Escribir contenido directamente
    $templateContent | Out-File -FilePath $fullPath -Encoding UTF8 -Force
    Write-Host "✅ Archivo creado: $relativePath" -ForegroundColor Green
}

# ---------------------------------------------------------
# 1. CONTENIDO: pom.xml (OPTIMIZADO)
# ---------------------------------------------------------
$pomXml = @'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0" 
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.2</version>
        <relativePath/>
    </parent>

    <groupId>com.tumi</groupId>
    <artifactId>tumipay-payin-service</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <name>tumipay-payin-service</name>
    <description>Componente de dominio reusable para procesamiento de transacciones Payln</description>

    <properties>
        <java.version>17</java.version>
        <org.mapstruct.version>1.5.5.Final</org.mapstruct.version>
        <org.projectlombok.version>1.18.30</org.projectlombok.version>
        <lombok-mapstruct-binding.version>0.2.0</lombok-mapstruct-binding.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <version>${org.projectlombok.version}</version>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>org.mapstruct</groupId>
            <artifactId>mapstruct</artifactId>
            <version>${org.mapstruct.version}</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                </configuration>
            </plugin>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <configuration>
                    <source>${java.version}</source>
                    <target>${java.version}</target>
                    <annotationProcessorPaths>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                            <version>${org.projectlombok.version}</version>
                        </path>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok-mapstruct-binding</artifactId>
                            <version>${lombok-mapstruct-binding.version}</version>
                        </path>
                        <path>
                            <groupId>org.mapstruct</groupId>
                            <artifactId>mapstruct-processor</artifactId>
                            <version>${org.mapstruct.version}</version>
                        </path>
                    </annotationProcessorPaths>
                </configuration>
            </plugin>
        </plugins>
    </build>
</project>
'@

# ---------------------------------------------------------
# 2. CONTENIDO: application.properties
# ---------------------------------------------------------
$appProps = @'
spring.application.name=tumipay-payin-service
server.port=8080
server.servlet.context-path=/api

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
# IMPORTANTE: validate para no dañar el esquema existente
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

# ---------------------------------------------------------
# 3. CONTENIDO: PayinServiceApplication.java
# ---------------------------------------------------------
$mainClass = @'
package com.tumi.payln;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class PayinServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(PayinServiceApplication.class, args);
    }
}
'@

# ---------------------------------------------------------
# 4. CONTENIDO: .gitignore
# ---------------------------------------------------------
$gitignore = @'
.idea/
*.iws
*.iml
*.ipr
.vscode/
.classpath
.project
.settings/
target/
build/
out/
bin/
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
*.log
logs/
.env
.env.local
.DS_Store
Thumbs.db
'@

# ---------------------------------------------------------
# 5. CONTENIDO: README.md
# ---------------------------------------------------------
$readme = @'
# TumiPay - PayIn Service

## Descripcion
Componente de dominio reusable para procesamiento de transacciones Payln

## Tecnologias
- Java 17
- Spring Boot 3.2.2
- PostgreSQL (NeonDB)
- Maven
- MapStruct
- Lombok

## Estructura
tumipay-payin-service/
  src/main/java/com/tumi/payln/
    domain/          # Logica de negocio
    application/     # Casos de uso
    infrastructure/  # Implementaciones

## Configuracion
1. Configurar NeonDB en application.properties
2. Ejecutar script SQL en la base de datos
3. mvn clean install
4. mvn spring-boot:run

## Endpoints
- POST /api/v1/payins
- GET /api/v1/payins/{id}
'@

# ---------------------------------------------------------
# EJECUCIÓN
# ---------------------------------------------------------
Write-Host "`nEscribiendo archivos de configuracion..." -ForegroundColor Cyan

# Escribir archivos
Write-FileFromTemplate "pom.xml" $pomXml
Write-FileFromTemplate "src\main\resources\application.properties" $appProps
Write-FileFromTemplate "src\main\java\com\tumi\payln\PayinServiceApplication.java" $mainClass
Write-FileFromTemplate ".gitignore" $gitignore
Write-FileFromTemplate "README.md" $readme

Write-Host "`nConfiguracion base completada." -ForegroundColor Green
Write-Host "✅ Se agrego lombok-mapstruct-binding al pom.xml para evitar errores de compilacion." -ForegroundColor Yellow
Write-Host "`nProximo paso:" -ForegroundColor Cyan
Write-Host "  cd '$basePath'" -ForegroundColor White
Write-Host "  mvn clean compile" -ForegroundColor White