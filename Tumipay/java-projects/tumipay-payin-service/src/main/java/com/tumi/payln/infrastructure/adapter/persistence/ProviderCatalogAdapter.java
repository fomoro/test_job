package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.application.port.IProviderCatalogPort;
import com.tumi.payln.domain.model.ProviderId;
import com.tumi.payln.infrastructure.persistence.repository.JpaProviderRepository;
import com.tumi.payln.infrastructure.persistence.entity.ProviderEntity;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class ProviderCatalogAdapter implements IProviderCatalogPort {
    
    private final JpaProviderRepository jpaProviderRepository;
    
    @Override
    public boolean isProviderActive(ProviderId providerId) {
        return jpaProviderRepository.findIsActiveByProviderId(providerId.value())
            .orElse(false);
    }
    
    @Override
    public String getProviderName(ProviderId providerId) {
        return jpaProviderRepository.findByProviderId(providerId.value())
            .map(ProviderEntity::getName)
            .orElse("Unknown Provider");
    }
}
