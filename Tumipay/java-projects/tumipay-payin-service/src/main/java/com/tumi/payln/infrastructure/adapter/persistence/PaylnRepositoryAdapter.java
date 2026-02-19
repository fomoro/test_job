package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.domain.model.PaylnTransaction;
import com.tumi.payln.domain.repository.IPaylnRepository;
import com.tumi.payln.infrastructure.persistence.entity.PaylnEntity;
import com.tumi.payln.infrastructure.persistence.mapper.PaylnMapper;
import com.tumi.payln.infrastructure.persistence.repository.JpaPaylnRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Repository;
import java.util.Optional;

/**
 * Adaptador que conecta el Puerto del Dominio (IPaylnRepository) con JPA.
 */
@Slf4j
@Repository
@RequiredArgsConstructor
public class PaylnRepositoryAdapter implements IPaylnRepository {
    
    private final JpaPaylnRepository jpaPaylnRepository;
    private final PaylnMapper paylnMapper;
    
    @Override
    public PaylnTransaction save(PaylnTransaction transaction) {
        log.debug("Saving Payln transaction: {}", transaction.getId().value());
        
        PaylnEntity entity = paylnMapper.toEntity(transaction);
        PaylnEntity savedEntity = jpaPaylnRepository.save(entity);
        
        return paylnMapper.toDomain(savedEntity);
    }
    
    @Override
    public Optional<PaylnTransaction> findById(PaylnId id) {
        log.debug("Finding Payln transaction by ID: {}", id.value());
        
        return jpaPaylnRepository.findByTransactionId(id.value())
            .map(paylnMapper::toDomain);
    }
    
    @Override
    public Optional<PaylnTransaction> findByIdempotencyKey(String idempotencyKey) {
        log.debug("Finding Payln transaction by idempotency key: {}", idempotencyKey);
        
        return jpaPaylnRepository.findByIdempotencyKey(idempotencyKey)
            .map(paylnMapper::toDomain);
    }
}
