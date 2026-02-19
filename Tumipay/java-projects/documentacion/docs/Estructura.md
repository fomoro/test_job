# 📁 **ESQUEMA FINAL AJUSTADO** (con base de datos real existente)

```
tumipay-payin-service/
├── pom.xml
├── src/main/java/com/tumi/payln/
│   ├── PayinServiceApplication.java         # SOLO esta clase de configuración
│   ├── domain/
│   │   ├── model/
│   │   │   ├── PaylnTransaction.java        # Aggregate Root
│   │   │   ├── PaylnId.java
│   │   │   ├── Amount.java
│   │   │   ├── Currency.java
│   │   │   ├── CustomerId.java
│   │   │   ├── AccountId.java
│   │   │   ├── ProviderId.java
│   │   │   ├── PaymentMethodId.java
│   │   │   ├── IdempotencyKey.java
│   │   │   └── PaylnStatus.java
│   │   ├── service/
│   │   │   ├── PaylnValidator.java
│   │   │   ├── PaylnStateMachine.java
│   │   │   └── IdempotencyService.java
│   │   └── repository/
│   │       └── IPaylnRepository.java
│   ├── application/
│   │   ├── dto/
│   │   │   ├── request/
│   │   │   │   ├── CreatePaylnRequest.java
│   │   │   │   └── QueryPaylnRequest.java
│   │   │   └── response/
│   │   │       ├── PaylnResponse.java
│   │   │       └── ErrorResponse.java
│   │   ├── port/
│   │   │   ├── IPaymentProviderPort.java
│   │   │   ├── IIdempotencyRepositoryPort.java
│   │   │   ├── ICustomerRepositoryPort.java
│   │   │   ├── IProviderCatalogPort.java
│   │   │   └── IPaymentMethodCatalogPort.java
│   │   ├── service/
│   │   │   ├── ProcessPaylnUseCase.java
│   │   │   ├── QueryPaylnUseCase.java
│   │   │   └── IdempotencyUseCase.java
│   │   └── exception/
│   │       ├── ApplicationException.java
│   │       ├── ValidationException.java
│   │       └── BusinessRuleException.java
│   └── infrastructure/
│       ├── persistence/
│       │   ├── entity/
│       │   │   ├── PaylnEntity.java
│       │   │   ├── CustomerEntity.java
│       │   │   ├── AccountEntity.java
│       │   │   ├── ProviderEntity.java
│       │   │   ├── PaymentMethodEntity.java
│       │   │   └── IdempotencyKeyEntity.java
│       │   ├── repository/
│       │   │   ├── JpaPaylnRepository.java
│       │   │   ├── JpaCustomerRepository.java
│       │   │   ├── JpaProviderRepository.java
│       │   │   ├── JpaPaymentMethodRepository.java
│       │   │   └── JpaIdempotencyRepository.java
│       │   └── mapper/
│       │       └── PaylnMapper.java
│       ├── adapter/
│       │   ├── persistence/      
│       │   │   ├── CustomerRepositoryAdapter.java    # Implementa ICustomerRepositoryPort
│       │   │   ├── IdempotencyRepositoryAdapter.java # Implementa IIdempotencyRepositoryPort
│       │   │   ├── ProviderCatalogAdapter.java       # Implementa IProviderCatalogPort
│       │   │   ├── PaymentMethodCatalogAdapter.java  # Implementa IPaymentMethodCatalogPort
│       │   │   └── PaylnRepositoryAdapter.java       # Implementa IPaylnRepository
│       │   ├── rest/
│       │   │   ├── controller/
│       │   │   │   ├── PaylnController.java
│       │   │   │   └── PaylnQueryController.java
│       │   │   ├── dto/
│       │   │   │   ├── PaylnRestRequest.java
│       │   │   │   └── PaylnRestResponse.java
│       │   │   └── handler/
│       │   │       └── GlobalExceptionHandler.java
│       │   ├── provider/
│       │   │   ├── PayUAdapter.java
│       │   │   ├── KushkiAdapter.java
│       │   │   └── StripeAdapter.java
│       │   └── factory/
│       │       └── PaymentProviderFactory.java
│       └── config/
│           └── DatabaseConfig.java           # SOLO si lo necesitas
└── src/main/resources/
    ├── application.properties
    └── (opcional) schema.sql
```

## 🔗 **RELACIONES CON TU BD EXISTENTE:**

```
Java Entity          ←→   Tabla PostgreSQL          Tipo
------------------------------------------------------------
CustomerEntity       ←→   clients                   Dominio
AccountEntity        ←→   accounts                  Dominio  
PaylnEntity          ←→   transactions              Dominio (Aggregate Root)
ProviderEntity       ←→   providers                 Catálogo
PaymentMethodEntity  ←→   payment_methods           Catálogo
IdempotencyKeyEntity ←→   idempotency_keys          Soporte
```