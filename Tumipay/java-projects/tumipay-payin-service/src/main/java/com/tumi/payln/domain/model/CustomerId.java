package com.tumi.payln.domain.model;

public record CustomerId(String value) {
    public CustomerId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Customer ID cannot be null or empty");
        }
    }
}
