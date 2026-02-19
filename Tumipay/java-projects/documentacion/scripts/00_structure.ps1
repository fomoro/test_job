# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Creando estructura del proyecto en: $basePath" -ForegroundColor Cyan

# ==========================================
# 1. CREACIÓN DE DIRECTORIOS
# ==========================================

# Definir las carpetas necesarias
$directories = @(
    "", # Raíz
    "src\main\resources",
    "src\main\java\com\tumi\payln",
    "src\main\java\com\tumi\payln\domain\model",
    "src\main\java\com\tumi\payln\domain\service",
    "src\main\java\com\tumi\payln\domain\repository",
    "src\main\java\com\tumi\payln\application\dto\request",
    "src\main\java\com\tumi\payln\application\dto\response",
    "src\main\java\com\tumi\payln\application\service",
    "src\main\java\com\tumi\payln\application\port",
    "src\main\java\com\tumi\payln\application\exception",
    "src\main\java\com\tumi\payln\infrastructure\persistence\entity",
    "src\main\java\com\tumi\payln\infrastructure\persistence\repository",
    "src\main\java\com\tumi\payln\infrastructure\persistence\mapper",
    "src\main\java\com\tumi\payln\infrastructure\adapter\persistence", # <--- NUEVA CARPETA
    "src\main\java\com\tumi\payln\infrastructure\adapter\rest\controller",
    "src\main\java\com\tumi\payln\infrastructure\adapter\rest\dto",
    "src\main\java\com\tumi\payln\infrastructure\adapter\rest\handler",
    "src\main\java\com\tumi\payln\infrastructure\adapter\provider",
    "src\main\java\com\tumi\payln\infrastructure\adapter\factory",
    "src\main\java\com\tumi\payln\infrastructure\config"
)

# Crear carpetas
foreach ($dir in $directories) {
    $fullPath = Join-Path -Path $basePath -ChildPath $dir
    New-Item -ItemType Directory -Force -Path $fullPath | Out-Null
    Write-Host "Carpeta creada: $dir" -ForegroundColor Green
}

# ==========================================
# 2. CREACIÓN DE ARCHIVOS (VACÍOS)
# ==========================================

# Función auxiliar para crear archivos
function Create-File {
    param ([string]$relativePath)
    $fullPath = Join-Path -Path $basePath -ChildPath $relativePath
    if (-not (Test-Path $fullPath)) {
        New-Item -Path $fullPath -ItemType File -Force | Out-Null
        Write-Host "Archivo creado: $relativePath" -ForegroundColor Gray
    }
}

# ==========================================
# 2.1 ARCHIVOS RAÍZ Y CONFIGURACIÓN
# ==========================================
Create-File "pom.xml"
Create-File "src\main\resources\application.properties"
Create-File "src\main\java\com\tumi\payln\PayinServiceApplication.java"

# ==========================================
# 2.2 DOMINIO - Value Objects y Entidades
# ==========================================
Create-File "src\main\java\com\tumi\payln\domain\model\PaylnTransaction.java"
Create-File "src\main\java\com\tumi\payln\domain\model\PaylnId.java"
Create-File "src\main\java\com\tumi\payln\domain\model\Amount.java"
Create-File "src\main\java\com\tumi\payln\domain\model\Currency.java"
Create-File "src\main\java\com\tumi\payln\domain\model\CustomerId.java"
Create-File "src\main\java\com\tumi\payln\domain\model\AccountId.java"
Create-File "src\main\java\com\tumi\payln\domain\model\ProviderId.java"
Create-File "src\main\java\com\tumi\payln\domain\model\PaymentMethodId.java"
Create-File "src\main\java\com\tumi\payln\domain\model\IdempotencyKey.java"
Create-File "src\main\java\com\tumi\payln\domain\model\PaylnStatus.java"

# ==========================================
# 2.3 DOMINIO - Servicios y Repositorios
# ==========================================
Create-File "src\main\java\com\tumi\payln\domain\service\PaylnValidator.java"
Create-File "src\main\java\com\tumi\payln\domain\service\PaylnStateMachine.java"
Create-File "src\main\java\com\tumi\payln\domain\service\IdempotencyService.java"
Create-File "src\main\java\com\tumi\payln\domain\repository\IPaylnRepository.java"

# ==========================================
# 2.4 APLICACIÓN - DTOs
# ==========================================
Create-File "src\main\java\com\tumi\payln\application\dto\request\CreatePaylnRequest.java"
Create-File "src\main\java\com\tumi\payln\application\dto\request\QueryPaylnRequest.java"
Create-File "src\main\java\com\tumi\payln\application\dto\response\PaylnResponse.java"
Create-File "src\main\java\com\tumi\payln\application\dto\response\ErrorResponse.java"

# ==========================================
# 2.5 APLICACIÓN - Puertos (Interfaces)
# ==========================================
Create-File "src\main\java\com\tumi\payln\application\port\IPaymentProviderPort.java"
Create-File "src\main\java\com\tumi\payln\application\port\IIdempotencyRepositoryPort.java"
Create-File "src\main\java\com\tumi\payln\application\port\ICustomerRepositoryPort.java"
Create-File "src\main\java\com\tumi\payln\application\port\IProviderCatalogPort.java"
Create-File "src\main\java\com\tumi\payln\application\port\IPaymentMethodCatalogPort.java"

# ==========================================
# 2.6 APLICACIÓN - Casos de Uso
# ==========================================
Create-File "src\main\java\com\tumi\payln\application\service\ProcessPaylnUseCase.java"
Create-File "src\main\java\com\tumi\payln\application\service\QueryPaylnUseCase.java"
Create-File "src\main\java\com\tumi\payln\application\service\IdempotencyUseCase.java"

# ==========================================
# 2.7 APLICACIÓN - Excepciones
# ==========================================
Create-File "src\main\java\com\tumi\payln\application\exception\ApplicationException.java"
Create-File "src\main\java\com\tumi\payln\application\exception\ValidationException.java"
Create-File "src\main\java\com\tumi\payln\application\exception\BusinessRuleException.java"

# ==========================================
# 2.8 INFRAESTRUCTURA - Entidades JPA
# ==========================================
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\entity\PaylnEntity.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\entity\CustomerEntity.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\entity\AccountEntity.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\entity\ProviderEntity.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\entity\PaymentMethodEntity.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\entity\IdempotencyKeyEntity.java"

# ==========================================
# 2.9 INFRAESTRUCTURA - Repositorios JPA
# ==========================================
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaPaylnRepository.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaCustomerRepository.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaAccountRepository.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaProviderRepository.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaPaymentMethodRepository.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\repository\JpaIdempotencyRepository.java"

# ==========================================
# 2.10 INFRAESTRUCTURA - Mappers
# ==========================================
Create-File "src\main\java\com\tumi\payln\infrastructure\persistence\mapper\PaylnMapper.java"

# ==========================================
# 2.11 INFRAESTRUCTURA - Persistence Adapters (Implementan Puertos)  <--- NUEVA SECCIÓN
# ==========================================
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\CustomerRepositoryAdapter.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\IdempotencyRepositoryAdapter.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\ProviderCatalogAdapter.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\PaymentMethodCatalogAdapter.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\PaylnRepositoryAdapter.java"

# ==========================================
# 2.12 INFRAESTRUCTURA - REST Adapters
# ==========================================
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\rest\controller\PaylnController.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\rest\controller\PaylnQueryController.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\rest\dto\PaylnRestRequest.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\rest\dto\PaylnRestResponse.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\rest\handler\GlobalExceptionHandler.java"

# ==========================================
# 2.13 INFRAESTRUCTURA - Provider Adapters
# ==========================================
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\provider\PayUAdapter.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\provider\KushkiAdapter.java"
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\provider\StripeAdapter.java"

# ==========================================
# 2.14 INFRAESTRUCTURA - Factory
# ==========================================
Create-File "src\main\java\com\tumi\payln\infrastructure\adapter\factory\PaymentProviderFactory.java"

Write-Host "✅ Estructura generada con éxito en: $basePath" -ForegroundColor Yellow