package com.tumi.payln.domain.model;

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
    
    // --- MÃ‰TODOS DE NEGOCIO ---
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
        // Flag para saber si es reconstrucciÃ³n desde BD
        private boolean isReconstituted = false; 
        
        public Builder id(PaylnId id) { transaction.id = id; return this; }
        public Builder customerId(CustomerId c) { transaction.customerId = c; return this; }
        public Builder accountId(AccountId a) { transaction.accountId = a; return this; }
        public Builder amount(Amount a) { transaction.amount = a; return this; }
        public Builder currency(Currency c) { transaction.currency = c; return this; }
        public Builder paymentMethodId(PaymentMethodId p) { transaction.paymentMethodId = p; return this; }
        public Builder providerId(ProviderId p) { transaction.providerId = p; return this; }
        public Builder idempotencyKey(IdempotencyKey k) { transaction.idempotencyKey = k; return this; }
        
        // MÃ©todos especiales para reconstrucciÃ³n desde Persistencia
        public Builder status(PaylnStatus s) { 
            transaction.status = s; 
            isReconstituted = true;
            return this; 
        }
        public Builder providerReference(String r) { transaction.providerReference = r; return this; }
        public Builder statusMessage(String m) { transaction.statusMessage = m; return this; }
        public Builder createdAt(LocalDateTime d) { transaction.createdAt = d; return this; }
        
        public PaylnTransaction build() {
            // Validaciones bÃ¡sicas
            if (transaction.id == null) transaction.id = PaylnId.generate();
            if (transaction.currency == null) transaction.currency = Currency.COP;
            
            // LÃ“GICA CORREGIDA:
            // Solo forzamos CREATED si es una transacciÃ³n NUEVA (no reconstruida)
            if (!isReconstituted) {
                transaction.status = PaylnStatus.CREATED;
                transaction.createdAt = LocalDateTime.now();
            }
            
            return transaction;
        }
    }
    
    public static Builder builder() { return new Builder(); }
}
