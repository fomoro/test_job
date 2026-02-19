package com.tumi.payln.infrastructure.persistence.entity;

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
}
