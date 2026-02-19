package com.tumi.payln.infrastructure.persistence.entity;

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
}
