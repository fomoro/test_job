package com.tumi.payln.domain.model;

import java.util.UUID;

public record IdempotencyKey(String value) {
    public IdempotencyKey {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Idempotency Key cannot be null or empty");
        }
        if (value.length() < 10 || value.length() > 100) {
            throw new IllegalArgumentException("Idempotency Key must be between 10 and 100 characters");
        }
    }
    
    public static IdempotencyKey generate() {
        return new IdempotencyKey("key-" + UUID.randomUUID().toString());
    }
}
