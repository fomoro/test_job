package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.application.port.ICustomerRepositoryPort;
import com.tumi.payln.domain.model.Customer;
import com.tumi.payln.domain.model.CustomerId;
import com.tumi.payln.infrastructure.persistence.entity.CustomerEntity;
import com.tumi.payln.infrastructure.persistence.repository.JpaCustomerRepository;
import com.tumi.payln.infrastructure.persistence.repository.JpaAccountRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Slf4j
@Component
@RequiredArgsConstructor
public class CustomerRepositoryAdapter implements ICustomerRepositoryPort {
    
    private final JpaCustomerRepository jpaCustomerRepository;
    private final JpaAccountRepository jpaAccountRepository;
    
    @Override
    public boolean exists(CustomerId customerId) {
        return jpaCustomerRepository.existsById(customerId.value());
    }
    
    @Override
    public boolean accountBelongsToCustomer(CustomerId customerId, String accountId) {
        return jpaCustomerRepository.existsAccountForCustomer(customerId.value(), accountId);
    }
    
    @Override
    public boolean isAccountActive(String accountId) {
        return jpaAccountRepository.findStatusByAccountId(accountId)
            .map(status -> "active".equalsIgnoreCase(status))
            .orElse(false);
    }
    
    @Override
    public Optional<String> findCustomerEmail(CustomerId customerId) {
        return jpaCustomerRepository.findById(customerId.value())
            .map(CustomerEntity::getEmail);
    }

    @Override
    public List<Customer> findAll() {
        return jpaCustomerRepository.findAll().stream()
            .map(entity -> Customer.builder()
                .id(new CustomerId(entity.getClientId()))
                .fullName(entity.getFullName())
                .email(entity.getEmail())
                .build())
            .collect(Collectors.toList());
    }
}
