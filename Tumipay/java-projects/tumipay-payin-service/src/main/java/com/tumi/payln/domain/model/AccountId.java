package com.tumi.payln.domain.model;

public record AccountId(String value) {
    public AccountId {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("Account ID cannot be null or empty");
        }
    }
}
