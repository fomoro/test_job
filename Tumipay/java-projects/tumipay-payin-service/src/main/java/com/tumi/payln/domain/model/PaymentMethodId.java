package com.tumi.payln.domain.model;

public record PaymentMethodId(String value) {
    public static final PaymentMethodId PSE = new PaymentMethodId("pse");
    public static final PaymentMethodId CREDIT_CARD = new PaymentMethodId("credit_card");
    public static final PaymentMethodId NEQUI = new PaymentMethodId("nequi");
    
    public PaymentMethodId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Payment Method ID cannot be null or empty");
        }
    }
}
