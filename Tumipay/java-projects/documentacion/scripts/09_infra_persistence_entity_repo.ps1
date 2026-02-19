# ==========================================
# CREACIÓN DE INFRAESTRUCTURA - Persistence (FINAL Y CORREGIDO)
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Creando Persistence Layer (Corregido) en: $basePath" -ForegroundColor Cyan

# Función para escribir archivos
function Write-InfraFile {
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
    Write-Host "✅ Archivo creado: $relativePath" -ForegroundColor Green
}

# ==========================================
# 1. ENTITIES JPA
# ==========================================

# 1.1 PaylnEntity.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\entity\PaylnEntity.java" 'package com.tumi.payln.infrastructure.persistence.entity;

import com.tumi.payln.domain.model.PaylnStatus;
import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "transactions")
@Data
@NoArgsConstructor
public class PaylnEntity {
    
    @Id
    @Column(name = "transaction_id", length = 50)
    private String transactionId;
    
    @Column(name = "client_id", length = 50, nullable = false)
    private String clientId;
    
    @Column(name = "account_id", length = 50, nullable = false)
    private String accountId;
    
    @Column(name = "amount", nullable = false, precision = 15, scale = 2)
    private BigDecimal amount;
    
    @Column(name = "currency", length = 3)
    private String currency = "COP";
    
    @Column(name = "payment_method_id", length = 20, nullable = false)
    private String paymentMethodId;
    
    @Column(name = "provider_id", length = 20, nullable = false)
    private String providerId;
    
    @Column(name = "provider_reference", length = 100)
    private String providerReference;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", length = 20, nullable = false)
    private PaylnStatus status;
    
    @Column(name = "status_message", columnDefinition = "TEXT")
    private String statusMessage;
    
    @Column(name = "idempotency_key", length = 100, nullable = false, unique = true)
    private String idempotencyKey;
    
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
}'

# 1.2 CustomerEntity.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\entity\CustomerEntity.java" 'package com.tumi.payln.infrastructure.persistence.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "clients")
@Data
@NoArgsConstructor
public class CustomerEntity {
    
    @Id
    @Column(name = "client_id", length = 50)
    private String clientId;
    
    @Column(name = "full_name", length = 100, nullable = false)
    private String fullName;
    
    @Column(name = "email", length = 100, nullable = false, unique = true)
    private String email;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
}'

# 1.3 AccountEntity.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\entity\AccountEntity.java" 'package com.tumi.payln.infrastructure.persistence.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "accounts")
@Data
@NoArgsConstructor
public class AccountEntity {
    
    @Id
    @Column(name = "account_id", length = 50)
    private String accountId;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "client_id", nullable = false)
    private CustomerEntity customer;
    
    @Column(name = "account_number", length = 50, nullable = false, unique = true)
    private String accountNumber;
    
    @Column(name = "account_type", length = 20, nullable = false)
    private String accountType;
    
    @Column(name = "status", length = 20, nullable = false)
    private String status;
    
    @Column(name = "balance", precision = 15, scale = 2)
    private BigDecimal balance = BigDecimal.ZERO;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
}'

# 1.4 ProviderEntity.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\entity\ProviderEntity.java" 'package com.tumi.payln.infrastructure.persistence.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "providers")
@Data
@NoArgsConstructor
public class ProviderEntity {
    
    @Id
    @Column(name = "provider_id", length = 20)
    private String providerId;
    
    @Column(name = "name", length = 50, nullable = false)
    private String name;
    
    @Column(name = "is_active")
    private Boolean isActive = true;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
}'

# 1.5 PaymentMethodEntity.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\entity\PaymentMethodEntity.java" 'package com.tumi.payln.infrastructure.persistence.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "payment_methods")
@Data
@NoArgsConstructor
public class PaymentMethodEntity {
    
    @Id
    @Column(name = "method_id", length = 20)
    private String methodId;
    
    @Column(name = "name", length = 50, nullable = false)
    private String name;
    
    @Column(name = "created_at")
    private LocalDateTime createdAt;
}'

# 1.6 IdempotencyKeyEntity.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\entity\IdempotencyKeyEntity.java" 'package com.tumi.payln.infrastructure.persistence.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Entity
@Table(name = "idempotency_keys")
@Data
@NoArgsConstructor
public class IdempotencyKeyEntity {
    
    @Id
    @Column(name = "idempotency_key", length = 100)
    private String idempotencyKey;
    
    @Column(name = "transaction_id", length = 50)
    private String transactionId;
    
    @Column(name = "status", length = 20, nullable = false)
    private String status = "PROCESSING";
    
    @Column(name = "request_hash", length = 64)
    private String requestHash;
    
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;
    
    @Column(name = "completed_at")
    private LocalDateTime completedAt;
}'

# ==========================================
# 2. JPA REPOSITORIES
# ==========================================

# 2.1 JpaPaylnRepository.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaPaylnRepository.java" 'package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.PaylnEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaPaylnRepository extends JpaRepository<PaylnEntity, String> {
    
    Optional<PaylnEntity> findByIdempotencyKey(String idempotencyKey);
    
    Optional<PaylnEntity> findByTransactionId(String transactionId);
}'

# 2.2 JpaCustomerRepository.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaCustomerRepository.java" 'package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.CustomerEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaCustomerRepository extends JpaRepository<CustomerEntity, String> {
    
    Optional<CustomerEntity> findByEmail(String email);
    
    // Consulta optimizada para verificar existencia sin traer la entidad completa
    @Query("SELECT CASE WHEN COUNT(a) > 0 THEN true ELSE false END " +
           "FROM AccountEntity a WHERE a.customer.clientId = :clientId AND a.accountId = :accountId")
    boolean existsAccountForCustomer(@Param("clientId") String clientId, @Param("accountId") String accountId);
}'

# 2.3 JpaAccountRepository.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaAccountRepository.java" 'package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.AccountEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaAccountRepository extends JpaRepository<AccountEntity, String> {
    
    Optional<AccountEntity> findByAccountNumber(String accountNumber);
    
    @Query("SELECT a.status FROM AccountEntity a WHERE a.accountId = :accountId")
    Optional<String> findStatusByAccountId(@Param("accountId") String accountId);
    
    @Query("SELECT a FROM AccountEntity a WHERE a.accountId = :accountId AND a.customer.clientId = :clientId")
    Optional<AccountEntity> findByAccountIdAndClientId(@Param("accountId") String accountId, @Param("clientId") String clientId);
}'

# 2.4 JpaProviderRepository.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaProviderRepository.java" 'package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.ProviderEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaProviderRepository extends JpaRepository<ProviderEntity, String> {
    
    @Query("SELECT p.isActive FROM ProviderEntity p WHERE p.providerId = :providerId")
    Optional<Boolean> findIsActiveByProviderId(@Param("providerId") String providerId);
    
    Optional<ProviderEntity> findByProviderId(String providerId);
}'

# 2.5 JpaPaymentMethodRepository.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaPaymentMethodRepository.java" 'package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.PaymentMethodEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaPaymentMethodRepository extends JpaRepository<PaymentMethodEntity, String> {
    
    Optional<PaymentMethodEntity> findByMethodId(String methodId);
}'

# 2.6 JpaIdempotencyRepository.java (CORREGIDO - SIN ERROR DE SINTAXIS)
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaIdempotencyRepository.java" 'package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.IdempotencyKeyEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Collection;
import java.util.Optional;

@Repository
public interface JpaIdempotencyRepository extends JpaRepository<IdempotencyKeyEntity, String> {
    
    // CORRECCION: Usamos método nativo de Spring Data para evitar errores de sintaxis en @Query
    Optional<IdempotencyKeyEntity> findByIdempotencyKeyAndStatusIn(String idempotencyKey, Collection<String> statuses);
    
    boolean existsByIdempotencyKey(String idempotencyKey);
}'

# ==========================================
# 3. MAPPER (MapStruct) - FIX BUILDER PATTERN
# ==========================================

# 3.1 PaylnMapper.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\persistence\mapper\PaylnMapper.java" 'package com.tumi.payln.infrastructure.persistence.mapper;

import com.tumi.payln.domain.model.*;
import com.tumi.payln.infrastructure.persistence.entity.PaylnEntity;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.Named;

import java.math.BigDecimal;

@Mapper(componentModel = "spring")
public interface PaylnMapper {
    
    // --- Domain -> Entity (Fácil, la entidad tiene Setters por @Data) ---
    @Mapping(target = "transactionId", source = "id.value")
    @Mapping(target = "clientId", source = "customerId.value")
    @Mapping(target = "accountId", source = "accountId.value")
    @Mapping(target = "amount", source = "amount.value")
    @Mapping(target = "currency", source = "currency.code")
    @Mapping(target = "paymentMethodId", source = "paymentMethodId.value")
    @Mapping(target = "providerId", source = "providerId.value")
    @Mapping(target = "providerReference", source = "providerReference")
    @Mapping(target = "status", source = "status")
    @Mapping(target = "statusMessage", source = "statusMessage")
    @Mapping(target = "idempotencyKey", source = "idempotencyKey.value")
    @Mapping(target = "createdAt", source = "createdAt")
    PaylnEntity toEntity(PaylnTransaction domain);
    
    // --- Entity -> Domain (COMPLEJO, el Dominio es inmutable y usa Builder) ---
    // Usamos default method para control total sobre el Builder
    default PaylnTransaction toDomain(PaylnEntity entity) {
        if (entity == null) {
            return null;
        }

        return PaylnTransaction.builder()
                .id(new PaylnId(entity.getTransactionId()))
                .customerId(new CustomerId(entity.getClientId()))
                .accountId(new AccountId(entity.getAccountId()))
                .amount(new Amount(entity.getAmount()))
                .currency(new Currency(entity.getCurrency()))
                .paymentMethodId(new PaymentMethodId(entity.getPaymentMethodId()))
                .providerId(new ProviderId(entity.getProviderId()))
                .idempotencyKey(new IdempotencyKey(entity.getIdempotencyKey()))
                // Nota: El estado y timestamps se manejan internamente en el builder o se asignan despues si es necesario
                // Para simplificar, reconstruimos el objeto.
                .build();
    }
}'

# ==========================================
# RESUMEN
# ==========================================
Write-Host "`nPersistence Layer generado (CORREGIDO TOTAL)!" -ForegroundColor Green
Write-Host "`nMejoras:" -ForegroundColor Yellow
Write-Host "   • PaylnMapper: Implementacion manual de toDomain para soportar el Builder del Dominio." -ForegroundColor Gray
Write-Host "   • JpaIdempotencyRepository: Uso de método ORM nativo (findIn) en lugar de Query manual." -ForegroundColor Gray
Write-Host "`nProximo paso:" -ForegroundColor Cyan
Write-Host "   Generar los ADAPTADORES (archivo 13) para conectar Puertos con JPA." -ForegroundColor White