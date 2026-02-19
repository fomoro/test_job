# ==========================================
# 20_fix_domain_status.ps1
# FIX: Permitir reconstruir estados desde BD sin resetear a CREATED
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Aplicando FIX de Estado en Dominio y Mapper..." -ForegroundColor Cyan

function Write-File {
    param ([string]$relativePath, [string]$content)
    $fullPath = Join-Path -Path $basePath -ChildPath $relativePath
    $content | Out-File -FilePath $fullPath -Encoding UTF8 -Force
    Write-Host "✅ Archivo corregido: $relativePath" -ForegroundColor Green
}

# 1. DOMINIO: Agregamos lógica para reconstruir objetos existentes
Write-File "src\main\java\com\tumi\payln\domain\model\PaylnTransaction.java" 'package com.tumi.payln.domain.model;

import java.time.LocalDateTime;

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
    
    private PaylnTransaction() {}
    
    // --- MÉTODOS DE NEGOCIO ---
    public void markAsValidated() {
        if (this.status != PaylnStatus.CREATED) {
            throw new IllegalStateException("Only CREATED transactions can be marked as VALIDATED.");
        }
        this.status = PaylnStatus.VALIDATED;
    }
    
    public void markAsProcessed(String providerReference) {
        if (this.status != PaylnStatus.VALIDATED) {
            throw new IllegalStateException("Only VALIDATED transactions can be processed.");
        }
        this.status = PaylnStatus.PROCESSED;
        this.providerReference = providerReference;
        this.statusMessage = "Transaction processed successfully";
    }
    
    public void markAsFailed(String errorMessage) {
        if (this.status.isTerminal()) return;
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
    
    // --- BUILDER PATTERN (FIXED) ---
    public static class Builder {
        private PaylnTransaction transaction = new PaylnTransaction();
        // Flag para saber si es reconstrucción desde BD
        private boolean isReconstituted = false; 
        
        public Builder id(PaylnId id) { transaction.id = id; return this; }
        public Builder customerId(CustomerId c) { transaction.customerId = c; return this; }
        public Builder accountId(AccountId a) { transaction.accountId = a; return this; }
        public Builder amount(Amount a) { transaction.amount = a; return this; }
        public Builder currency(Currency c) { transaction.currency = c; return this; }
        public Builder paymentMethodId(PaymentMethodId p) { transaction.paymentMethodId = p; return this; }
        public Builder providerId(ProviderId p) { transaction.providerId = p; return this; }
        public Builder idempotencyKey(IdempotencyKey k) { transaction.idempotencyKey = k; return this; }
        
        // Métodos especiales para reconstrucción desde Persistencia
        public Builder status(PaylnStatus s) { 
            transaction.status = s; 
            isReconstituted = true;
            return this; 
        }
        public Builder providerReference(String r) { transaction.providerReference = r; return this; }
        public Builder statusMessage(String m) { transaction.statusMessage = m; return this; }
        public Builder createdAt(LocalDateTime d) { transaction.createdAt = d; return this; }
        
        public PaylnTransaction build() {
            // Validaciones básicas
            if (transaction.id == null) transaction.id = PaylnId.generate();
            if (transaction.currency == null) transaction.currency = Currency.COP;
            
            // LÓGICA CORREGIDA:
            // Solo forzamos CREATED si es una transacción NUEVA (no reconstruida)
            if (!isReconstituted) {
                transaction.status = PaylnStatus.CREATED;
                transaction.createdAt = LocalDateTime.now();
            }
            
            return transaction;
        }
    }
    
    public static Builder builder() { return new Builder(); }
}'

# 2. MAPPER: Actualizamos para usar los campos de estado
Write-File "src\main\java\com\tumi\payln\infrastructure\persistence\mapper\PaylnMapper.java" 'package com.tumi.payln.infrastructure.persistence.mapper;

import com.tumi.payln.domain.model.*;
import com.tumi.payln.infrastructure.persistence.entity.PaylnEntity;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface PaylnMapper {
    
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
    
    default PaylnTransaction toDomain(PaylnEntity entity) {
        if (entity == null) return null;

        return PaylnTransaction.builder()
                .id(new PaylnId(entity.getTransactionId()))
                .customerId(new CustomerId(entity.getClientId()))
                .accountId(new AccountId(entity.getAccountId()))
                .amount(new Amount(entity.getAmount()))
                .currency(new Currency(entity.getCurrency()))
                .paymentMethodId(new PaymentMethodId(entity.getPaymentMethodId()))
                .providerId(new ProviderId(entity.getProviderId()))
                .idempotencyKey(new IdempotencyKey(entity.getIdempotencyKey()))
                // AQUI ESTA LA CORRECCION: Pasamos el estado y datos históricos
                .status(entity.getStatus())
                .providerReference(entity.getProviderReference())
                .statusMessage(entity.getStatusMessage())
                .createdAt(entity.getCreatedAt())
                .build();
    }
}'

Write-Host "✅ Corrección aplicada." -ForegroundColor Yellow
Write-Host "1. Detén el servidor." -ForegroundColor Gray
Write-Host "2. Ejecuta: mvn clean spring-boot:run" -ForegroundColor White