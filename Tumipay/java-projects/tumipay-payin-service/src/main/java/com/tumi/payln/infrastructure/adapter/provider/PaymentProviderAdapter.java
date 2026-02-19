package com.tumi.payln.infrastructure.adapter.provider;

import com.tumi.payln.application.port.IPaymentProviderPort;
import com.tumi.payln.domain.model.Amount;
import com.tumi.payln.domain.model.ProviderId;
import com.tumi.payln.infrastructure.adapter.factory.PaymentProviderFactory;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

@Slf4j
@Primary 
@Component
@RequiredArgsConstructor
public class PaymentProviderAdapter implements IPaymentProviderPort {
    
    private final PaymentProviderFactory paymentProviderFactory;
    
    @Override
    public PaymentResult processPayment(ProviderId providerId, Amount amount, PaymentRequest request) {
        log.debug("Routing payment to provider: {}", providerId.value());
        
        IPaymentProviderPort provider = paymentProviderFactory.getProvider(providerId);
        return provider.processPayment(providerId, amount, request);
    }
}
