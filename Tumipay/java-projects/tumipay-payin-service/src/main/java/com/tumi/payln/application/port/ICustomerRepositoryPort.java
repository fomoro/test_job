package com.tumi.payln.application.port;

import com.tumi.payln.domain.model.Customer;
import com.tumi.payln.domain.model.CustomerId;
import java.util.List;
import java.util.Optional;

public interface ICustomerRepositoryPort {
    
    boolean exists(CustomerId customerId);
    
    boolean accountBelongsToCustomer(CustomerId customerId, String accountId);
    
    boolean isAccountActive(String accountId);
    
    Optional<String> findCustomerEmail(CustomerId customerId);

    // NUEVO MÃƒÆ’Ã†â€™ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â°TODO
    List<Customer> findAll();
}
