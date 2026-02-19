package com.tumi.payln.infrastructure.adapter.rest.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PaylnRestResponse {
    
    @JsonProperty("transaction_id")
    private String transactionId;
    
    @JsonProperty("client_id")
    private String clientId;
    
    @JsonProperty("account_id")
    private String accountId;
    
    private BigDecimal amount;
    private String currency;
    
    @JsonProperty("payment_method_id")
    private String paymentMethodId;
    
    @JsonProperty("provider_id")
    private String providerId;
    
    @JsonProperty("provider_reference")
    private String providerReference;
    
    private String status;
    
    @JsonProperty("status_message")
    private String statusMessage;
    
    @JsonProperty("idempotency_key")
    private String idempotencyKey;
    
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonProperty("created_at")
    private LocalDateTime createdAt;
}
