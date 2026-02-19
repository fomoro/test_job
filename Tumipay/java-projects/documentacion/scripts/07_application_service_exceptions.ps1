# ==========================================
# CREACIÓN DE APLICACIÓN - Parte 2: Services y Exceptions (OPTIMIZADO)
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Creando Services y Exceptions (Optimizado) en: $basePath" -ForegroundColor Cyan

# Función para escribir archivos
function Write-AppFile {
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
# 1. EXCEPCIONES
# ==========================================

# 1.1 ApplicationException.java
Write-AppFile "src\main\java\com\tumi\payln\application\exception\ApplicationException.java" 'package com.tumi.payln.application.exception;

/**
 * Excepción base de la aplicación (Runtime para no ensuciar firmas de métodos).
 */
public class ApplicationException extends RuntimeException {
    
    public ApplicationException(String message) {
        super(message);
    }
    
    public ApplicationException(String message, Throwable cause) {
        super(message, cause);
    }
}'

# 1.2 ValidationException.java
Write-AppFile "src\main\java\com\tumi\payln\application\exception\ValidationException.java" 'package com.tumi.payln.application.exception;

/**
 * Excepción para errores de validación de entrada (HTTP 400).
 */
public class ValidationException extends ApplicationException {
    
    public ValidationException(String message) {
        super(message);
    }
    
    public ValidationException(String message, Throwable cause) {
        super(message, cause);
    }
}'

# 1.3 BusinessRuleException.java
Write-AppFile "src\main\java\com\tumi\payln\application\exception\BusinessRuleException.java" 'package com.tumi.payln.application.exception;

/**
 * Excepción para violaciones de reglas de negocio (HTTP 409 o 422).
 */
public class BusinessRuleException extends ApplicationException {
    
    public BusinessRuleException(String message) {
        super(message);
    }
    
    public BusinessRuleException(String message, Throwable cause) {
        super(message, cause);
    }
}'

# ==========================================
# 2. SERVICIOS (Use Cases)
# ==========================================

# 2.1 ProcessPaylnUseCase.java
Write-AppFile "src\main\java\com\tumi\payln\application\service\ProcessPaylnUseCase.java" 'package com.tumi.payln.application.service;

import com.tumi.payln.application.dto.request.CreatePaylnRequest;
import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.exception.BusinessRuleException;
import com.tumi.payln.application.exception.ValidationException;
import com.tumi.payln.application.exception.ApplicationException;
import com.tumi.payln.application.port.*;
import com.tumi.payln.domain.model.*;
import com.tumi.payln.domain.repository.IPaylnRepository;
import com.tumi.payln.domain.service.IdempotencyService;
import com.tumi.payln.domain.service.PaylnStateMachine;
import com.tumi.payln.domain.service.PaylnValidator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Optional;

/**
 * Orquestador principal para procesar transacciones.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ProcessPaylnUseCase {
    
    private final IPaylnRepository paylnRepository;
    private final IPaymentProviderPort paymentProviderPort;
    private final IIdempotencyRepositoryPort idempotencyRepository;
    private final ICustomerRepositoryPort customerRepository;
    private final IProviderCatalogPort providerCatalog;
    private final IPaymentMethodCatalogPort paymentMethodCatalog;
    
    // Servicios de Dominio
    private final PaylnValidator paylnValidator;
    private final PaylnStateMachine stateMachine;
    private final IdempotencyService idempotencyService;
    
    @Transactional
    public PaylnResponse execute(CreatePaylnRequest request, String idempotencyKeyValue) {
        log.info("Processing Payln transaction for client: {}", request.getClientId());
        
        // 1. Validar formato de Idempotencia (Dominio puro)
        IdempotencyKey idempotencyKey = new IdempotencyKey(idempotencyKeyValue);
        idempotencyService.validateKeyFormat(idempotencyKey);
        
        // 2. Verificar duplicados (Infraestructura)
        if (idempotencyRepository.exists(idempotencyKey)) {
             Optional<PaylnTransaction> existingTx = paylnRepository.findByIdempotencyKey(idempotencyKeyValue);
             if (existingTx.isPresent()) {
                 log.info("Idempotent request match - returning existing transaction");
                 return mapToResponse(existingTx.get());
             }
             throw new ValidationException("Idempotency key already used but transaction not found.");
        }
        
        // 3. Validar Inputs y Catálogos
        validateInput(request);
        
        // 4. Construir Agregado
        PaylnTransaction transaction = createTransaction(request, idempotencyKey);
        
        // 5. Validar Reglas de Negocio (Cliente, Cuentas, Saldos, etc.)
        validateBusinessRules(transaction);
        
        // 6. Ejecutar Proceso Transaccional
        return processTransaction(transaction);
    }
    
    private void validateInput(CreatePaylnRequest request) {
        if (request.getAmount() == null || request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            throw new ValidationException("Invalid amount");
        }
        
        ProviderId providerId = new ProviderId(request.getProviderId());
        if (!providerCatalog.isProviderActive(providerId)) {
            throw new ValidationException("Provider is not active or does not exist: " + request.getProviderId());
        }
        
        PaymentMethodId paymentMethodId = new PaymentMethodId(request.getPaymentMethodId());
        if (!paymentMethodCatalog.exists(paymentMethodId)) {
            throw new ValidationException("Invalid payment method: " + request.getPaymentMethodId());
        }
    }
    
    private PaylnTransaction createTransaction(CreatePaylnRequest request, IdempotencyKey idempotencyKey) {
        return PaylnTransaction.builder()
            .customerId(new CustomerId(request.getClientId()))
            .accountId(new AccountId(request.getAccountId()))
            .amount(new Amount(request.getAmount()))
            .currency(new Currency(request.getCurrency()))
            .paymentMethodId(new PaymentMethodId(request.getPaymentMethodId()))
            .providerId(new ProviderId(request.getProviderId()))
            .idempotencyKey(idempotencyKey)
            .build();
    }
    
    private void validateBusinessRules(PaylnTransaction transaction) {
        CustomerId customerId = transaction.getCustomerId();
        
        if (!customerRepository.exists(customerId)) {
            throw new BusinessRuleException("Customer not found");
        }
        
        if (!customerRepository.accountBelongsToCustomer(customerId, transaction.getAccountId().value())) {
            throw new BusinessRuleException("Account does not belong to customer");
        }
        
        if (!customerRepository.isAccountActive(transaction.getAccountId().value())) {
            throw new BusinessRuleException("Account is not active");
        }
        
        // Validación final de dominio
        paylnValidator.validateTransaction(transaction);
    }
    
    private PaylnResponse processTransaction(PaylnTransaction transaction) {
        try {
            // A. Guardar estado inicial (CREATED)
            paylnRepository.save(transaction);
            idempotencyRepository.save(transaction.getIdempotencyKey(), transaction.getId());
            
            // B. Validar y Guardar (VALIDATED)
            stateMachine.transitionToValidated(transaction);
            paylnRepository.save(transaction);
            
            // C. Preparar datos para el proveedor
            String customerEmail = customerRepository.findCustomerEmail(transaction.getCustomerId())
                .orElseThrow(() -> new BusinessRuleException("Customer email not found"));
            
            IPaymentProviderPort.PaymentRequest paymentRequest = new IPaymentProviderPort.PaymentRequest(
                transaction.getCustomerId().value(),
                customerEmail,
                transaction.getAccountId().value()
            );
            
            // D. Llamada al Proveedor Externo
            IPaymentProviderPort.PaymentResult result = paymentProviderPort.processPayment(
                transaction.getProviderId(),
                transaction.getAmount(),
                paymentRequest
            );
            
            // E. Transición de estado basada en respuesta
            if (result.success()) {
                stateMachine.transitionToProcessed(transaction, result.providerReference());
            } else {
                stateMachine.transitionToFailed(transaction, result.message());
            }
            
            // F. Guardar estado final
            PaylnTransaction savedTx = paylnRepository.save(transaction);
            log.info("Transaction finished with status: {}", savedTx.getStatus());
            
            return mapToResponse(savedTx);
            
        } catch (BusinessRuleException | ValidationException e) {
            // Errores de negocio conocidos: Solo relanzar, el @Transactional hará rollback si es necesario
            // Ojo: Si ya guardamos CREATED, quizás queramos marcar FAILED en lugar de rollback total.
            // Para esta prueba, marcaremos FAILED para dejar rastro.
            handleSystemError(transaction, e);
            throw e; 
            
        } catch (Exception e) {
            // Errores inesperados
            handleSystemError(transaction, e);
            throw new ApplicationException("System error processing transaction: " + e.getMessage(), e);
        }
    }
    
    private void handleSystemError(PaylnTransaction transaction, Exception e) {
        log.error("Error processing transaction {}: {}", transaction.getId().value(), e.getMessage());
        try {
            transaction.markAsFailed(e.getMessage());
            paylnRepository.save(transaction);
        } catch (Exception persistenceError) {
            log.error("FATAL: Could not save failed state", persistenceError);
        }
    }
    
    // Mapeo manual (simple y efectivo para no depender de mappers externos en la lógica core)
    private PaylnResponse mapToResponse(PaylnTransaction transaction) {
        PaylnResponse response = new PaylnResponse();
        response.setTransactionId(transaction.getId().value());
        response.setClientId(transaction.getCustomerId().value());
        response.setAccountId(transaction.getAccountId().value());
        response.setAmount(transaction.getAmount().value());
        response.setCurrency(transaction.getCurrency().code());
        response.setPaymentMethodId(transaction.getPaymentMethodId().value());
        response.setProviderId(transaction.getProviderId().value());
        response.setProviderReference(transaction.getProviderReference());
        response.setStatus(transaction.getStatus().name());
        response.setStatusMessage(transaction.getStatusMessage());
        response.setIdempotencyKey(transaction.getIdempotencyKey().value());
        response.setCreatedAt(transaction.getCreatedAt());
        return response;
    }
}'

# 2.2 QueryPaylnUseCase.java
Write-AppFile "src\main\java\com\tumi\payln\application\service\QueryPaylnUseCase.java" 'package com.tumi.payln.application.service;

import com.tumi.payln.application.dto.request.QueryPaylnRequest;
import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.exception.ApplicationException;
import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.domain.model.PaylnTransaction;
import com.tumi.payln.domain.repository.IPaylnRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class QueryPaylnUseCase {
    
    private final IPaylnRepository paylnRepository;
    
    public PaylnResponse execute(QueryPaylnRequest request) {
        PaylnId transactionId = new PaylnId(request.getTransactionId());
        
        return paylnRepository.findById(transactionId)
            .map(this::mapToResponse)
            .orElseThrow(() -> new ApplicationException("Transaction not found with ID: " + request.getTransactionId()));
    }
    
    private PaylnResponse mapToResponse(PaylnTransaction transaction) {
        PaylnResponse response = new PaylnResponse();
        response.setTransactionId(transaction.getId().value());
        response.setClientId(transaction.getCustomerId().value());
        response.setAccountId(transaction.getAccountId().value());
        response.setAmount(transaction.getAmount().value());
        response.setCurrency(transaction.getCurrency().code());
        response.setPaymentMethodId(transaction.getPaymentMethodId().value());
        response.setProviderId(transaction.getProviderId().value());
        response.setProviderReference(transaction.getProviderReference());
        response.setStatus(transaction.getStatus().name());
        response.setStatusMessage(transaction.getStatusMessage());
        response.setIdempotencyKey(transaction.getIdempotencyKey().value());
        response.setCreatedAt(transaction.getCreatedAt());
        return response;
    }
}'

# 2.3 IdempotencyUseCase.java
Write-AppFile "src\main\java\com\tumi\payln\application\service\IdempotencyUseCase.java" 'package com.tumi.payln.application.service;

import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.port.IIdempotencyRepositoryPort;
import com.tumi.payln.domain.model.IdempotencyKey;
import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.domain.model.PaylnTransaction;
import com.tumi.payln.domain.repository.IPaylnRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class IdempotencyUseCase {
    
    private final IIdempotencyRepositoryPort idempotencyRepository;
    private final IPaylnRepository paylnRepository;
    
    public Optional<PaylnResponse> checkIdempotency(String idempotencyKeyValue) {
        IdempotencyKey idempotencyKey = new IdempotencyKey(idempotencyKeyValue);
        
        return idempotencyRepository.findTransactionIdByKey(idempotencyKey)
            .flatMap(paylnRepository::findById)
            .map(this::mapToResponse);
    }
    
    private PaylnResponse mapToResponse(PaylnTransaction transaction) {
        PaylnResponse response = new PaylnResponse();
        response.setTransactionId(transaction.getId().value());
        response.setClientId(transaction.getCustomerId().value());
        response.setAccountId(transaction.getAccountId().value());
        response.setAmount(transaction.getAmount().value());
        response.setCurrency(transaction.getCurrency().code());
        response.setPaymentMethodId(transaction.getPaymentMethodId().value());
        response.setProviderId(transaction.getProviderId().value());
        response.setProviderReference(transaction.getProviderReference());
        response.setStatus(transaction.getStatus().name());
        response.setStatusMessage(transaction.getStatusMessage());
        response.setIdempotencyKey(transaction.getIdempotencyKey().value());
        response.setCreatedAt(transaction.getCreatedAt());
        return response;
    }
}'

Write-Host "✅ Servicios de Aplicación generados correctamente." -ForegroundColor Green
Write-Host "👉 Siguiente paso: Generar la capa de INFRAESTRUCTURA (JPA Entities y Repositorios)." -ForegroundColor Yellow