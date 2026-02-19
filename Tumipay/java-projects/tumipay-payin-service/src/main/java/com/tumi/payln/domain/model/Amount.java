package com.tumi.payln.domain.model;

import java.math.BigDecimal;
import java.math.RoundingMode;

public record Amount(BigDecimal value) {
    public static final BigDecimal MIN_AMOUNT = new BigDecimal("0.01");
    public static final BigDecimal MAX_AMOUNT = new BigDecimal("5000000.00");
    
    public Amount {
        if (value == null) {
            throw new IllegalArgumentException("Amount cannot be null");
        }
        if (value.compareTo(MIN_AMOUNT) < 0) {
            throw new IllegalArgumentException("Amount must be greater than 0");
        }
        if (value.compareTo(MAX_AMOUNT) > 0) {
            throw new IllegalArgumentException("Amount exceeds maximum limit");
        }
        // Asegurar siempre 2 decimales para manejo monetario preciso
        value = value.setScale(2, RoundingMode.HALF_UP);
    }
}
