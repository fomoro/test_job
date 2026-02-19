package com.tumi.payln.infrastructure.persistence.entity;

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
}
