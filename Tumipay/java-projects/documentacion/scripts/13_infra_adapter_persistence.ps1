# ==========================================
# CREACIÓN DE ADAPTADORES DE INFRAESTRUCTURA - Persistence 
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Creando Adaptadores de Persistence (Corregido) en: $basePath" -ForegroundColor Cyan

# Función para escribir archivos
function Write-AdapterFile {
    param (
        [string]$relativePath, 
        [string]$content
    )
    $fullPath = Join-Path -Path $basePath -ChildPath $relativePath
    
    $parentDir = Split-Path -Parent $fullPath
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
    }

    $content | Out-File -FilePath $fullPath -Encoding UTF8 -Force
    Write-Host "✅ Adaptador creado: $relativePath" -ForegroundColor Green
}

# Crear la carpeta persistence dentro de adapter si no existe
$adapterPersistencePath = Join-Path $basePath "src\main\java\com\tumi\payln\infrastructure\adapter\persistence"
if (-not (Test-Path $adapterPersistencePath)) {
    New-Item -ItemType Directory -Force -Path $adapterPersistencePath | Out-Null
}

# ==========================================
# 1. PaylnRepositoryAdapter.java
# ==========================================
Write-AdapterFile "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\PaylnRepositoryAdapter.java" 'package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.domain.model.PaylnTransaction;
import com.tumi.payln.domain.repository.IPaylnRepository;
import com.tumi.payln.infrastructure.persistence.entity.PaylnEntity;
import com.tumi.payln.infrastructure.persistence.mapper.PaylnMapper;
import com.tumi.payln.infrastructure.persistence.repository.JpaPaylnRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;
import java.util.Optional;

/**
 * Adaptador que conecta el Puerto del Dominio (IPaylnRepository) con JPA.
 */
@Slf4j
@Repository
@RequiredArgsConstructor
public class PaylnRepositoryAdapter implements IPaylnRepository {
    
    private final JpaPaylnRepository jpaPaylnRepository;
    private final PaylnMapper paylnMapper;
    
    @Override
    public PaylnTransaction save(PaylnTransaction transaction) {
        log.debug("Saving Payln transaction: {}", transaction.getId().value());
        
        PaylnEntity entity = paylnMapper.toEntity(transaction);
        PaylnEntity savedEntity = jpaPaylnRepository.save(entity);
        
        return paylnMapper.toDomain(savedEntity);
    }
    
    @Override
    public Optional<PaylnTransaction> findById(PaylnId id) {
        log.debug("Finding Payln transaction by ID: {}", id.value());
        
        return jpaPaylnRepository.findByTransactionId(id.value())
            .map(paylnMapper::toDomain);
    }
    
    @Override
    public Optional<PaylnTransaction> findByIdempotencyKey(String idempotencyKey) {
        log.debug("Finding Payln transaction by idempotency key: {}", idempotencyKey);
        
        return jpaPaylnRepository.findByIdempotencyKey(idempotencyKey)
            .map(paylnMapper::toDomain);
    }
}'

# ==========================================
# 2. CustomerRepositoryAdapter.java
# ==========================================
Write-AdapterFile "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\CustomerRepositoryAdapter.java" 'package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.application.port.ICustomerRepositoryPort;
import com.tumi.payln.domain.model.CustomerId;
import com.tumi.payln.infrastructure.persistence.entity.CustomerEntity;
import com.tumi.payln.infrastructure.persistence.repository.JpaCustomerRepository;
import com.tumi.payln.infrastructure.persistence.repository.JpaAccountRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import java.util.Optional;

/**
 * Adaptador para validaciones de Clientes y Cuentas.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class CustomerRepositoryAdapter implements ICustomerRepositoryPort {
    
    private final JpaCustomerRepository jpaCustomerRepository;
    private final JpaAccountRepository jpaAccountRepository;
    
    @Override
    public boolean exists(CustomerId customerId) {
        return jpaCustomerRepository.existsById(customerId.value());
    }
    
    @Override
    public boolean accountBelongsToCustomer(CustomerId customerId, String accountId) {
        return jpaCustomerRepository.existsAccountForCustomer(customerId.value(), accountId);
    }
    
    @Override
    public boolean isAccountActive(String accountId) {
        return jpaAccountRepository.findStatusByAccountId(accountId)
            .map(status -> "active".equalsIgnoreCase(status))
            .orElse(false);
    }
    
    @Override
    public Optional<String> findCustomerEmail(CustomerId customerId) {
        return jpaCustomerRepository.findById(customerId.value())
            .map(CustomerEntity::getEmail);
    }
}'

# ==========================================
# 3. IdempotencyRepositoryAdapter.java (CORREGIDO)
# ==========================================
Write-AdapterFile "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\IdempotencyRepositoryAdapter.java" 'package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.application.port.IIdempotencyRepositoryPort;
import com.tumi.payln.domain.model.IdempotencyKey;
import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.infrastructure.persistence.entity.IdempotencyKeyEntity;
import com.tumi.payln.infrastructure.persistence.repository.JpaIdempotencyRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Slf4j
@Component
@RequiredArgsConstructor
public class IdempotencyRepositoryAdapter implements IIdempotencyRepositoryPort {
    
    private final JpaIdempotencyRepository jpaIdempotencyRepository;
    
    // CORRECCION: Definimos la lista de estados válidos para usar el método ORM
    private static final List<String> COMPLETED_STATUSES = List.of("COMPLETED", "PROCESSED");

    @Override
    public void save(IdempotencyKey key, PaylnId transactionId) {
        log.debug("Saving idempotency key: {}", key.value());
        
        IdempotencyKeyEntity entity = new IdempotencyKeyEntity();
        entity.setIdempotencyKey(key.value());
        entity.setTransactionId(transactionId.value());
        entity.setStatus("COMPLETED");
        entity.setCreatedAt(LocalDateTime.now());
        entity.setCompletedAt(LocalDateTime.now());
        
        jpaIdempotencyRepository.save(entity);
    }
    
    @Override
    public Optional<PaylnId> findTransactionIdByKey(IdempotencyKey key) {
        // CORRECCION: Llamada al nuevo método seguro sin SQL manual
        return jpaIdempotencyRepository.findByIdempotencyKeyAndStatusIn(key.value(), COMPLETED_STATUSES)
            .map(entity -> new PaylnId(entity.getTransactionId()));
    }
    
    @Override
    public boolean exists(IdempotencyKey key) {
        return jpaIdempotencyRepository.existsByIdempotencyKey(key.value());
    }
}'

# ==========================================
# 4. ProviderCatalogAdapter.java
# ==========================================
Write-AdapterFile "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\ProviderCatalogAdapter.java" 'package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.application.port.IProviderCatalogPort;
import com.tumi.payln.domain.model.ProviderId;
import com.tumi.payln.infrastructure.persistence.repository.JpaProviderRepository;
import com.tumi.payln.infrastructure.persistence.entity.ProviderEntity;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class ProviderCatalogAdapter implements IProviderCatalogPort {
    
    private final JpaProviderRepository jpaProviderRepository;
    
    @Override
    public boolean isProviderActive(ProviderId providerId) {
        return jpaProviderRepository.findIsActiveByProviderId(providerId.value())
            .orElse(false);
    }
    
    @Override
    public String getProviderName(ProviderId providerId) {
        return jpaProviderRepository.findByProviderId(providerId.value())
            .map(ProviderEntity::getName)
            .orElse("Unknown Provider");
    }
}'

# ==========================================
# 5. PaymentMethodCatalogAdapter.java
# ==========================================
Write-AdapterFile "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\PaymentMethodCatalogAdapter.java" 'package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.application.port.IPaymentMethodCatalogPort;
import com.tumi.payln.domain.model.PaymentMethodId;
import com.tumi.payln.infrastructure.persistence.repository.JpaPaymentMethodRepository;
import com.tumi.payln.infrastructure.persistence.entity.PaymentMethodEntity;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class PaymentMethodCatalogAdapter implements IPaymentMethodCatalogPort {
    
    private final JpaPaymentMethodRepository jpaPaymentMethodRepository;
    
    @Override
    public boolean exists(PaymentMethodId paymentMethodId) {
        return jpaPaymentMethodRepository.existsById(paymentMethodId.value());
    }
    
    @Override
    public String getPaymentMethodName(PaymentMethodId paymentMethodId) {
        return jpaPaymentMethodRepository.findByMethodId(paymentMethodId.value())
            .map(PaymentMethodEntity::getName)
            .orElse("Unknown Payment Method");
    }
}'

Write-Host "✅ Adaptadores de Persistencia (CORREGIDOS) generados correctamente." -ForegroundColor Green
Write-Host "👉 Siguiente paso: Ejecutar 'mvn clean compile' para verificar integridad total." -ForegroundColor Yellow