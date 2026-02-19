package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.application.port.IPaymentMethodCatalogPort;
import com.tumi.payln.domain.model.PaymentMethodId;
import com.tumi.payln.infrastructure.persistence.repository.JpaPaymentMethodRepository;
import com.tumi.payln.infrastructure.persistence.entity.PaymentMethodEntity;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class PaymentMethodCatalogAdapter implements IPaymentMethodCatalogPort {
    
    private final JpaPaymentMethodRepository jpaPaymentMethodRepository;
    
    @Override
    public boolean exists(PaymentMethodId paymentMethodId) {
        return jpaPaymentMethodRepository.existsById(paymentMethodId.value());
    }
    
    @Override
    public String getPaymentMethodName(PaymentMethodId paymentMethodId) {
        return jpaPaymentMethodRepository.findByMethodId(paymentMethodId.value())
            .map(PaymentMethodEntity::getName)
            .orElse("Unknown Payment Method");
    }
}
