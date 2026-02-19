package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.AccountEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaAccountRepository extends JpaRepository<AccountEntity, String> {
    
    Optional<AccountEntity> findByAccountNumber(String accountNumber);
    
    @Query("SELECT a.status FROM AccountEntity a WHERE a.accountId = :accountId")
    Optional<String> findStatusByAccountId(@Param("accountId") String accountId);
    
    @Query("SELECT a FROM AccountEntity a WHERE a.accountId = :accountId AND a.customer.clientId = :clientId")
    Optional<AccountEntity> findByAccountIdAndClientId(@Param("accountId") String accountId, @Param("clientId") String clientId);
}
