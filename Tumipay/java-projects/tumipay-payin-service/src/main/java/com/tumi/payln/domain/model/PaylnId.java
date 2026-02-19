package com.tumi.payln.domain.model;

import java.util.UUID;

public record PaylnId(String value) {
    public PaylnId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Payln ID cannot be null or empty");
        }
        if (value.length() > 50) {
            throw new IllegalArgumentException("Payln ID cannot exceed 50 characters");
        }
    }
    
    public static PaylnId generate() {
        return new PaylnId("tx-" + UUID.randomUUID().toString());
    }
}
