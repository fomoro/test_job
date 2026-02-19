package com.tumi.payln.application.service;

import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.port.IIdempotencyRepositoryPort;
import com.tumi.payln.domain.model.IdempotencyKey;
import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.domain.model.PaylnTransaction;
import com.tumi.payln.domain.repository.IPaylnRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class IdempotencyUseCase {
    
    private final IIdempotencyRepositoryPort idempotencyRepository;
    private final IPaylnRepository paylnRepository;
    
    public Optional<PaylnResponse> checkIdempotency(String idempotencyKeyValue) {
        IdempotencyKey idempotencyKey = new IdempotencyKey(idempotencyKeyValue);
        
        return idempotencyRepository.findTransactionIdByKey(idempotencyKey)
            .flatMap(paylnRepository::findById)
            .map(this::mapToResponse);
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
