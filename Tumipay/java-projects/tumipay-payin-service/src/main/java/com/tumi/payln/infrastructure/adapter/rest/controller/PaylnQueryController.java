package com.tumi.payln.infrastructure.adapter.rest.controller;

import com.tumi.payln.application.dto.request.QueryPaylnRequest;
import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.service.QueryPaylnUseCase;
import com.tumi.payln.infrastructure.adapter.rest.dto.PaylnRestResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/payins")
public class PaylnQueryController {
    
    private final QueryPaylnUseCase queryPaylnUseCase;
    
    @GetMapping("/{transaction_id}")
    public ResponseEntity<PaylnRestResponse> getPayln(@PathVariable("transaction_id") String transactionId) {
        
        QueryPaylnRequest request = new QueryPaylnRequest();
        request.setTransactionId(transactionId);
        
        PaylnResponse r = queryPaylnUseCase.execute(request);
        
        PaylnRestResponse response = new PaylnRestResponse(
            r.getTransactionId(), r.getClientId(), r.getAccountId(), r.getAmount(),
            r.getCurrency(), r.getPaymentMethodId(), r.getProviderId(), r.getProviderReference(),
            r.getStatus(), r.getStatusMessage(), r.getIdempotencyKey(), r.getCreatedAt()
        );
        
        return ResponseEntity.ok(response);
    }
}
