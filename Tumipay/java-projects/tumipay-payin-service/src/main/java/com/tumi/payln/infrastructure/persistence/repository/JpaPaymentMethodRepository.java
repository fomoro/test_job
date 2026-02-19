package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.PaymentMethodEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaPaymentMethodRepository extends JpaRepository<PaymentMethodEntity, String> {
    
    Optional<PaymentMethodEntity> findByMethodId(String methodId);
}
