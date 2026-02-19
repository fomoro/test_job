# ==========================================
# CREACIÓN DE DOMINIO - Value Objects y Aggregate Root
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Creando dominio en: $basePath" -ForegroundColor Cyan

# Función para escribir archivos de dominio
function Write-DomainFile {
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
    Write-Host "✅ Dominio creado: $relativePath" -ForegroundColor Green
}

# ==========================================
# 1. VALUE OBJECTS
# ==========================================

# 1.1 PaylnId.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\PaylnId.java" @'
package com.tumi.payln.domain.model;

import java.util.UUID;

public record PaylnId(String value) {
    public PaylnId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Payln ID cannot be null or empty");
        }
        if (value.length() > 50) {
            throw new IllegalArgumentException("Payln ID cannot exceed 50 characters");
        }
    }
    
    public static PaylnId generate() {
        return new PaylnId("tx-" + UUID.randomUUID().toString());
    }
}
'@

# 1.2 Amount.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\Amount.java" @'
package com.tumi.payln.domain.model;

import java.math.BigDecimal;
import java.math.RoundingMode;

public record Amount(BigDecimal value) {
    public static final BigDecimal MIN_AMOUNT = new BigDecimal("0.01");
    public static final BigDecimal MAX_AMOUNT = new BigDecimal("5000000.00");
    
    public Amount {
        if (value == null) {
            throw new IllegalArgumentException("Amount cannot be null");
        }
        if (value.compareTo(MIN_AMOUNT) < 0) {
            throw new IllegalArgumentException("Amount must be greater than 0");
        }
        if (value.compareTo(MAX_AMOUNT) > 0) {
            throw new IllegalArgumentException("Amount exceeds maximum limit");
        }
        // Asegurar siempre 2 decimales para manejo monetario preciso
        value = value.setScale(2, RoundingMode.HALF_UP);
    }
}
'@

# 1.3 Currency.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\Currency.java" @'
package com.tumi.payln.domain.model;

public record Currency(String code) {
    public static final Currency COP = new Currency("COP");
    public static final Currency USD = new Currency("USD");
    
    public Currency {
        if (code == null || code.length() != 3) {
            throw new IllegalArgumentException("Currency code must be 3 characters");
        }
    }
}
'@

# 1.4 CustomerId.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\CustomerId.java" @'
package com.tumi.payln.domain.model;

public record CustomerId(String value) {
    public CustomerId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Customer ID cannot be null or empty");
        }
    }
}
'@

# 1.5 AccountId.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\AccountId.java" @'
package com.tumi.payln.domain.model;

public record AccountId(String value) {
    public AccountId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Account ID cannot be null or empty");
        }
    }
}
'@

# 1.6 ProviderId.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\ProviderId.java" @'
package com.tumi.payln.domain.model;

public record ProviderId(String value) {
    public static final ProviderId PAYU = new ProviderId("payu");
    public static final ProviderId KUSHKI = new ProviderId("kushki");
    public static final ProviderId STRIPE = new ProviderId("stripe");
    
    public ProviderId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Provider ID cannot be null or empty");
        }
    }
}
'@

# 1.7 PaymentMethodId.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\PaymentMethodId.java" @'
package com.tumi.payln.domain.model;

public record PaymentMethodId(String value) {
    public static final PaymentMethodId PSE = new PaymentMethodId("pse");
    public static final PaymentMethodId CREDIT_CARD = new PaymentMethodId("credit_card");
    public static final PaymentMethodId NEQUI = new PaymentMethodId("nequi");
    
    public PaymentMethodId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Payment Method ID cannot be null or empty");
        }
    }
}
'@

# 1.8 IdempotencyKey.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\IdempotencyKey.java" @'
package com.tumi.payln.domain.model;

import java.util.UUID;

public record IdempotencyKey(String value) {
    public IdempotencyKey {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Idempotency Key cannot be null or empty");
        }
        if (value.length() < 10 || value.length() > 100) {
            throw new IllegalArgumentException("Idempotency Key must be between 10 and 100 characters");
        }
    }
    
    public static IdempotencyKey generate() {
        return new IdempotencyKey("key-" + UUID.randomUUID().toString());
    }
}
'@

# 1.9 PaylnStatus.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\PaylnStatus.java" @'
package com.tumi.payln.domain.model;

public enum PaylnStatus {
    CREATED,
    VALIDATED,
    PROCESSED,
    FAILED;
    
    public boolean isTerminal() {
        return this == PROCESSED || this == FAILED;
    }
}
'@

# ==========================================
# 2. AGGREGATE ROOT - PaylnTransaction.java
# ==========================================
Write-DomainFile "src\main\java\com\tumi\payln\domain\model\PaylnTransaction.java" @'
package com.tumi.payln.domain.model;

import java.time.LocalDateTime;

/**
 * Aggregate Root que representa una transacción Payln.
 * Encapsula todas las reglas de negocio y transiciones de estado.
 */
public class PaylnTransaction {
    private PaylnId id;
    private CustomerId customerId;
    private AccountId accountId;
    private Amount amount;
    private Currency currency;
    private PaymentMethodId paymentMethodId;
    private ProviderId providerId;
    private PaylnStatus status;
    private String providerReference;
    private String statusMessage;
    private IdempotencyKey idempotencyKey;
    private LocalDateTime createdAt;
    
    // Constructor privado para usar Builder
    private PaylnTransaction() {}
    
    // --- MÉTODOS DE NEGOCIO (State Transitions) ---
    
    // Renombrado de validate() a markAsValidated() para evitar confusión con validadores lógicos
    public void markAsValidated() {
        if (this.status != PaylnStatus.CREATED) {
            throw new IllegalStateException("Only CREATED transactions can be marked as VALIDATED. Current: " + this.status);
        }
        this.status = PaylnStatus.VALIDATED;
    }
    
    public void markAsProcessed(String providerReference) {
        if (this.status != PaylnStatus.VALIDATED) {
            throw new IllegalStateException("Only VALIDATED transactions can be processed. Current: " + this.status);
        }
        if (providerReference == null || providerReference.isBlank()) {
            throw new IllegalArgumentException("Provider reference is required for PROCESSED state");
        }
        this.status = PaylnStatus.PROCESSED;
        this.providerReference = providerReference;
        this.statusMessage = "Transaction processed successfully";
    }
    
    public void markAsFailed(String errorMessage) {
        // Un fallo puede ocurrir desde cualquier estado no terminal
        if (this.status.isTerminal()) {
             throw new IllegalStateException("Cannot fail a transaction that is already terminal: " + this.status);
        }
        this.status = PaylnStatus.FAILED;
        this.statusMessage = errorMessage;
    }
    
    // --- GETTERS ---
    public PaylnId getId() { return id; }
    public CustomerId getCustomerId() { return customerId; }
    public AccountId getAccountId() { return accountId; }
    public Amount getAmount() { return amount; }
    public Currency getCurrency() { return currency; }
    public PaymentMethodId getPaymentMethodId() { return paymentMethodId; }
    public ProviderId getProviderId() { return providerId; }
    public PaylnStatus getStatus() { return status; }
    public String getProviderReference() { return providerReference; }
    public String getStatusMessage() { return statusMessage; }
    public IdempotencyKey getIdempotencyKey() { return idempotencyKey; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    
    // --- BUILDER PATTERN ---
    public static class Builder {
        private PaylnTransaction transaction = new PaylnTransaction();
        
        public Builder id(PaylnId id) {
            transaction.id = id;
            return this;
        }
        
        public Builder customerId(CustomerId customerId) {
            transaction.customerId = customerId;
            return this;
        }
        
        public Builder accountId(AccountId accountId) {
            transaction.accountId = accountId;
            return this;
        }
        
        public Builder amount(Amount amount) {
            transaction.amount = amount;
            return this;
        }
        
        public Builder currency(Currency currency) {
            transaction.currency = currency;
            return this;
        }
        
        public Builder paymentMethodId(PaymentMethodId paymentMethodId) {
            transaction.paymentMethodId = paymentMethodId;
            return this;
        }
        
        public Builder providerId(ProviderId providerId) {
            transaction.providerId = providerId;
            return this;
        }
        
        public Builder idempotencyKey(IdempotencyKey idempotencyKey) {
            transaction.idempotencyKey = idempotencyKey;
            return this;
        }
        
        public PaylnTransaction build() {
            // Validaciones de integridad estructural
            if (transaction.id == null) transaction.id = PaylnId.generate();
            if (transaction.customerId == null) throw new IllegalArgumentException("Customer ID is required");
            if (transaction.accountId == null) throw new IllegalArgumentException("Account ID is required");
            if (transaction.amount == null) throw new IllegalArgumentException("Amount is required");
            if (transaction.currency == null) transaction.currency = Currency.COP;
            if (transaction.paymentMethodId == null) throw new IllegalArgumentException("Payment Method ID is required");
            if (transaction.providerId == null) throw new IllegalArgumentException("Provider ID is required");
            if (transaction.idempotencyKey == null) throw new IllegalArgumentException("Idempotency Key is required");
            
            // Estado inicial siempre CREATED
            transaction.status = PaylnStatus.CREATED;
            transaction.createdAt = LocalDateTime.now();
            
            return transaction;
        }
    }
    
    public static Builder builder() {
        return new Builder();
    }
}
'@

# ==========================================
# 3. SERVICIOS DE DOMINIO
# ==========================================

# 3.1 PaylnValidator.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\service\PaylnValidator.java" @'
package com.tumi.payln.domain.service;

import com.tumi.payln.domain.model.*;

public class PaylnValidator {
    
    public void validateTransaction(PaylnTransaction transaction) {
        // Validaciones de negocio puras
        validateAmount(transaction.getAmount());
        validateCurrency(transaction.getCurrency());
    }
    
    private void validateAmount(Amount amount) {
        if (amount == null) {
            throw new IllegalArgumentException("Amount is required");
        }
        // Aquí podrían ir reglas más complejas, ej: límites por tipo de usuario
    }
    
    private void validateCurrency(Currency currency) {
        if (currency == null) {
            throw new IllegalArgumentException("Currency is required");
        }
        if (!currency.code().equals("COP")) {
            throw new IllegalArgumentException("Only COP currency is supported");
        }
    }
}
'@

# 3.2 PaylnStateMachine.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\service\PaylnStateMachine.java" @'
package com.tumi.payln.domain.service;

import com.tumi.payln.domain.model.PaylnStatus;
import com.tumi.payln.domain.model.PaylnTransaction;

public class PaylnStateMachine {
    
    public void transitionToValidated(PaylnTransaction transaction) {
        // Delega al Aggregate Root
        transaction.markAsValidated();
    }
    
    public void transitionToProcessed(PaylnTransaction transaction, String providerReference) {
        // Delega al Aggregate Root
        transaction.markAsProcessed(providerReference);
    }
    
    public void transitionToFailed(PaylnTransaction transaction, String errorMessage) {
        // Delega al Aggregate Root
        transaction.markAsFailed(errorMessage);
    }
}
'@

# 3.3 IdempotencyService.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\service\IdempotencyService.java" @'
package com.tumi.payln.domain.service;

import com.tumi.payln.domain.model.IdempotencyKey;

public class IdempotencyService {
    
    // Este servicio en el dominio define la lógica pura de las llaves
    public void validateKeyFormat(IdempotencyKey idempotencyKey) {
        if (idempotencyKey == null) {
            throw new IllegalArgumentException("Idempotency key is required");
        }
    }
    
    public IdempotencyKey generateIdempotencyKey() {
        return IdempotencyKey.generate();
    }
}
'@

# ==========================================
# 4. REPOSITORIO DE DOMINIO
# ==========================================

# 4.1 IPaylnRepository.java
Write-DomainFile "src\main\java\com\tumi\payln\domain\repository\IPaylnRepository.java" @'
package com.tumi.payln.domain.repository;

import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.domain.model.PaylnTransaction;
import java.util.Optional;

public interface IPaylnRepository {
    
    PaylnTransaction save(PaylnTransaction transaction);
    
    Optional<PaylnTransaction> findById(PaylnId id);
    
    Optional<PaylnTransaction> findByIdempotencyKey(String idempotencyKey);
}
'@

Write-Host "`nDominio creado exitosamente!" -ForegroundColor Green