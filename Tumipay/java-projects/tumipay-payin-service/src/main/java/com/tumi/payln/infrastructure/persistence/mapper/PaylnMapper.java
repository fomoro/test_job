package com.tumi.payln.infrastructure.persistence.mapper;

import com.tumi.payln.domain.model.*;
import com.tumi.payln.infrastructure.persistence.entity.PaylnEntity;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;

@Mapper(componentModel = "spring")
public interface PaylnMapper {
    
    @Mapping(target = "transactionId", source = "id.value")
    @Mapping(target = "clientId", source = "customerId.value")
    @Mapping(target = "accountId", source = "accountId.value")
    @Mapping(target = "amount", source = "amount.value")
    @Mapping(target = "currency", source = "currency.code")
    @Mapping(target = "paymentMethodId", source = "paymentMethodId.value")
    @Mapping(target = "providerId", source = "providerId.value")
    @Mapping(target = "providerReference", source = "providerReference")
    @Mapping(target = "status", source = "status")
    @Mapping(target = "statusMessage", source = "statusMessage")
    @Mapping(target = "idempotencyKey", source = "idempotencyKey.value")
    @Mapping(target = "createdAt", source = "createdAt")
    PaylnEntity toEntity(PaylnTransaction domain);
    
    default PaylnTransaction toDomain(PaylnEntity entity) {
        if (entity == null) return null;

        return PaylnTransaction.builder()
                .id(new PaylnId(entity.getTransactionId()))
                .customerId(new CustomerId(entity.getClientId()))
                .accountId(new AccountId(entity.getAccountId()))
                .amount(new Amount(entity.getAmount()))
                .currency(new Currency(entity.getCurrency()))
                .paymentMethodId(new PaymentMethodId(entity.getPaymentMethodId()))
                .providerId(new ProviderId(entity.getProviderId()))
                .idempotencyKey(new IdempotencyKey(entity.getIdempotencyKey()))
                // AQUI ESTA LA CORRECCION: Pasamos el estado y datos histÃ³ricos
                .status(entity.getStatus())
                .providerReference(entity.getProviderReference())
                .statusMessage(entity.getStatusMessage())
                .createdAt(entity.getCreatedAt())
                .build();
    }
}
