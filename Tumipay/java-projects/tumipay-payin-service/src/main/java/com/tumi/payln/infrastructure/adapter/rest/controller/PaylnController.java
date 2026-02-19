package com.tumi.payln.infrastructure.adapter.rest.controller;

import com.tumi.payln.application.dto.request.CreatePaylnRequest;
import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.service.ProcessPaylnUseCase;
import com.tumi.payln.infrastructure.adapter.rest.dto.PaylnRestRequest;
import com.tumi.payln.infrastructure.adapter.rest.dto.PaylnRestResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/payins")
public class PaylnController {
    
    private final ProcessPaylnUseCase processPaylnUseCase;
    
    @PostMapping
    public ResponseEntity<PaylnRestResponse> createPayln(
            @Valid @RequestBody PaylnRestRequest restRequest,
            @RequestHeader(value = "x-idempotency-key", required = false) String idempotencyKey) {
        
        log.info("Received Payln request: client={}", restRequest.getClientId());
        
        String finalIdempotencyKey = (idempotencyKey != null && !idempotencyKey.isBlank()) 
            ? idempotencyKey 
            : "key-" + UUID.randomUUID().toString();
        
        CreatePaylnRequest appRequest = new CreatePaylnRequest();
        appRequest.setClientId(restRequest.getClientId());
        appRequest.setAccountId(restRequest.getAccountId());
        appRequest.setAmount(restRequest.getAmount());
        appRequest.setCurrency(restRequest.getCurrency());
        appRequest.setPaymentMethodId(restRequest.getPaymentMethodId());
        appRequest.setProviderId(restRequest.getProviderId());
        
        PaylnResponse appResponse = processPaylnUseCase.execute(appRequest, finalIdempotencyKey);
        
        return ResponseEntity.status(HttpStatus.CREATED)
                .header("x-idempotency-key", finalIdempotencyKey)
                .body(mapToRestResponse(appResponse));
    }
    
    private PaylnRestResponse mapToRestResponse(PaylnResponse r) {
        return new PaylnRestResponse(
            r.getTransactionId(), r.getClientId(), r.getAccountId(), r.getAmount(),
            r.getCurrency(), r.getPaymentMethodId(), r.getProviderId(), r.getProviderReference(),
            r.getStatus(), r.getStatusMessage(), r.getIdempotencyKey(), r.getCreatedAt()
        );
    }
}
