package com.tumi.payln.domain.model;

public record ProviderId(String value) {
    public static final ProviderId PAYU = new ProviderId("payu");
    public static final ProviderId KUSHKI = new ProviderId("kushki");
    public static final ProviderId STRIPE = new ProviderId("stripe");
    
    public ProviderId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Provider ID cannot be null or empty");
        }
    }
}
