package com.tumi.payln.application.port;

import com.tumi.payln.domain.model.IdempotencyKey;
import com.tumi.payln.domain.model.PaylnId;
import java.util.Optional;

/**
 * Puerto para el repositorio de idempotencia.
 */
public interface IIdempotencyRepositoryPort {
    
    void save(IdempotencyKey key, PaylnId transactionId);
    
    Optional<PaylnId> findTransactionIdByKey(IdempotencyKey key);
    
    boolean exists(IdempotencyKey key);
}
