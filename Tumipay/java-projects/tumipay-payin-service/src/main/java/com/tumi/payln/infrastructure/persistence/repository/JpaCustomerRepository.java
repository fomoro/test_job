package com.tumi.payln.infrastructure.persistence.repository;

import com.tumi.payln.infrastructure.persistence.entity.CustomerEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;

@Repository
public interface JpaCustomerRepository extends JpaRepository<CustomerEntity, String> {
    
    Optional<CustomerEntity> findByEmail(String email);
    
    // Consulta optimizada para verificar existencia sin traer la entidad completa
    @Query("SELECT CASE WHEN COUNT(a) > 0 THEN true ELSE false END " +
           "FROM AccountEntity a WHERE a.customer.clientId = :clientId AND a.accountId = :accountId")
    boolean existsAccountForCustomer(@Param("clientId") String clientId, @Param("accountId") String accountId);
}
