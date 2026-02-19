package com.tumi.payln.infrastructure.adapter.provider;

import com.tumi.payln.application.port.IPaymentProviderPort;
import com.tumi.payln.domain.model.Amount;
import com.tumi.payln.domain.model.ProviderId;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import java.util.UUID;

@Slf4j
@Component
public class StripeAdapter implements IPaymentProviderPort {
    
    @Override
    public PaymentResult processPayment(ProviderId providerId, Amount amount, PaymentRequest request) {
        log.info("--> [Stripe] Processing payment: client={}, amount={} (Converted to USD)", request.clientId(), amount.value());
        
        try {
            Thread.sleep(80);
            String ref = "ch_" + UUID.randomUUID().toString().replace("-", "");
            return new PaymentResult(true, ref, "Succeeded via Stripe");
        } catch (Exception e) {
            return new PaymentResult(false, null, "Stripe Error: " + e.getMessage());
        }
    }
}
