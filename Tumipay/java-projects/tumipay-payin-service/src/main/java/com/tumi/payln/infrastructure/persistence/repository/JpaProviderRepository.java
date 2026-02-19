package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.ProviderEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaProviderRepository extends JpaRepository<ProviderEntity, String> {
    
    @Query("SELECT p.isActive FROM ProviderEntity p WHERE p.providerId = :providerId")
    Optional<Boolean> findIsActiveByProviderId(@Param("providerId") String providerId);
    
    Optional<ProviderEntity> findByProviderId(String providerId);
}
