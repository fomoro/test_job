package com.tumi.payln.domain.model;

public record Currency(String code) {
    public static final Currency COP = new Currency("COP");
    public static final Currency USD = new Currency("USD");
    
    public Currency {
        if (code == null || code.length() != 3) {
            throw new IllegalArgumentException("Currency code must be 3 characters");
        }
    }
}
