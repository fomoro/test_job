package com.tumi.payln.application.service;

import com.tumi.payln.application.port.ICustomerRepositoryPort;
import com.tumi.payln.domain.model.Customer;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ListClientsUseCase {
    
    private final ICustomerRepositoryPort customerRepository;
    
    public List<Customer> execute() {
        return customerRepository.findAll();
    }
}
