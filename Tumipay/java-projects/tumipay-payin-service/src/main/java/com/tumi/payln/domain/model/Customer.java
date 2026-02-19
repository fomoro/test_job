package com.tumi.payln.domain.model;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Builder;

@Getter
@Builder
@AllArgsConstructor
public class Customer {
    private final CustomerId id;
    private final String fullName;
    private final String email;
}
