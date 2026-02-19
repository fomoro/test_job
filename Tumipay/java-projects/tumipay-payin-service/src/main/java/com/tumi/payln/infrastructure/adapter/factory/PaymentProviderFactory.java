package com.tumi.payln.infrastructure.adapter.factory;

import com.tumi.payln.application.port.IPaymentProviderPort;
import com.tumi.payln.domain.model.ProviderId;
import com.tumi.payln.infrastructure.adapter.provider.*;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class PaymentProviderFactory {
    
    private final PayUAdapter payUAdapter;
    private final KushkiAdapter kushkiAdapter;
    private final StripeAdapter stripeAdapter;
    
    public IPaymentProviderPort getProvider(ProviderId providerId) {
        return switch (providerId.value()) {
            case "payu" -> payUAdapter;
            case "kushki" -> kushkiAdapter;
            case "stripe" -> stripeAdapter;
            default -> throw new IllegalArgumentException("Unsupported provider: " + providerId.value());
        };
    }
}
