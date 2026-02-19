package com.tumi.payln.infrastructure.adapter.rest.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;

@Data
@NoArgsConstructor
public class PaylnRestRequest {
    
    @JsonProperty("client_id")
    @NotBlank(message = "client_id is required")
    private String clientId;
    
    @JsonProperty("account_id")
    @NotBlank(message = "account_id is required")
    private String accountId;
    
    @NotNull(message = "amount is required")
    @DecimalMin(value = "0.01", message = "amount must be greater than 0")
    private BigDecimal amount;
    
    private String currency = "COP";
    
    @JsonProperty("payment_method_id")
    @NotBlank(message = "payment_method_id is required")
    private String paymentMethodId;
    
    @JsonProperty("provider_id")
    @NotBlank(message = "provider_id is required")
    private String providerId;
}
