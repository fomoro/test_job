package com.tumi.payln.domain.repository;

import com.tumi.payln.domain.model.PaylnId;
import com.tumi.payln.domain.model.PaylnTransaction;
import java.util.Optional;

public interface IPaylnRepository {
    
    PaylnTransaction save(PaylnTransaction transaction);
    
    Optional<PaylnTransaction> findById(PaylnId id);
    
    Optional<PaylnTransaction> findByIdempotencyKey(String idempotencyKey);
}
