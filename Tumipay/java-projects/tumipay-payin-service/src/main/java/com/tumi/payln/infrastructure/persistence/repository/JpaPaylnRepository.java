package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.PaylnEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaPaylnRepository extends JpaRepository<PaylnEntity, String> {
    
    Optional<PaylnEntity> findByIdempotencyKey(String idempotencyKey);
    
    Optional<PaylnEntity> findByTransactionId(String transactionId);
}
