package com.tumi.payln.application.service;

import com.tumi.payln.application.dto.request.QueryPaylnRequest;
import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.exception.ApplicationException;
import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.domain.model.PaylnTransaction;
import com.tumi.payln.domain.repository.IPaylnRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class QueryPaylnUseCase {
    
    private final IPaylnRepository paylnRepository;
    
    public PaylnResponse execute(QueryPaylnRequest request) {
        PaylnId transactionId = new PaylnId(request.getTransactionId());
        
        return paylnRepository.findById(transactionId)
            .map(this::mapToResponse)
            .orElseThrow(() -> new ApplicationException("Transaction not found with ID: " + request.getTransactionId()));
    }
    
    private PaylnResponse mapToResponse(PaylnTransaction transaction) {
        PaylnResponse response = new PaylnResponse();
        response.setTransactionId(transaction.getId().value());
        response.setClientId(transaction.getCustomerId().value());
        response.setAccountId(transaction.getAccountId().value());
        response.setAmount(transaction.getAmount().value());
        response.setCurrency(transaction.getCurrency().code());
        response.setPaymentMethodId(transaction.getPaymentMethodId().value());
        response.setProviderId(transaction.getProviderId().value());
        response.setProviderReference(transaction.getProviderReference());
        response.setStatus(transaction.getStatus().name());
        response.setStatusMessage(transaction.getStatusMessage());
        response.setIdempotencyKey(transaction.getIdempotencyKey().value());
        response.setCreatedAt(transaction.getCreatedAt());
        return response;
    }
}
