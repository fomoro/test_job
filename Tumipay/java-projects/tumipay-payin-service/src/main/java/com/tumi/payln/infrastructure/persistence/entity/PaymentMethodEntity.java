package com.tumi.payln.infrastructure.persistence.entity;

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
}
