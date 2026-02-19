# ==========================================
# 16_infra_config_domain.ps1
# Configuración de Beans de Dominio (Clean Architecture)
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Creando configuración de Dominio en: $basePath" -ForegroundColor Cyan

function Write-ConfigFile {
    param ([string]$relativePath, [string]$content)
    $fullPath = Join-Path -Path $basePath -ChildPath $relativePath
    $parentDir = Split-Path -Parent $fullPath
    if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Force -Path $parentDir | Out-Null }
    $content | Out-File -FilePath $fullPath -Encoding UTF8 -Force
    Write-Host "✅ Archivo creado: $relativePath" -ForegroundColor Green
}

# 1. DomainConfig.java
Write-ConfigFile "src\main\java\com\tumi\payln\infrastructure\config\DomainConfig.java" 'package com.tumi.payln.infrastructure.config;

import com.tumi.payln.domain.service.IdempotencyService;
import com.tumi.payln.domain.service.PaylnStateMachine;
import com.tumi.payln.domain.service.PaylnValidator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * CONFIGURACIÓN DE DOMINIO
 * * Registra los servicios de dominio puros como Beans de Spring.
 * Esto mantiene el paquete "domain" libre de dependencias del framework (Clean Architecture).
 */
@Configuration
public class DomainConfig {

    @Bean
    public PaylnValidator paylnValidator() {
        return new PaylnValidator();
    }

    @Bean
    public PaylnStateMachine paylnStateMachine() {
        return new PaylnStateMachine();
    }

    @Bean
    public IdempotencyService idempotencyService() {
        return new IdempotencyService();
    }
}'

Write-Host "`n✅ Configuración de Dominio aplicada." -ForegroundColor Yellow
Write-Host "Ahora Spring podrá ver e inyectar tus servicios de dominio." -ForegroundColor Gray
Write-Host "`nPrueba nuevamente:" -ForegroundColor Cyan
Write-Host "mvn spring-boot:run" -ForegroundColor White