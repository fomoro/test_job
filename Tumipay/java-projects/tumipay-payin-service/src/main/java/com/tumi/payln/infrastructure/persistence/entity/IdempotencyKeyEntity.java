package com.tumi.payln.infrastructure.persistence.entity;

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
}
