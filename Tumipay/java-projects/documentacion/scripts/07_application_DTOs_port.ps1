# ==========================================
# CREACIÓN DE APLICACIÓN - Parte 1: DTOs y Ports (OPTIMIZADO)
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Creando DTOs y Ports (con Lombok y Validaciones) en: $basePath" -ForegroundColor Cyan

# Función para escribir archivos
function Write-AppFile {
    param (
        [string]$relativePath, 
        [string]$content
    )
    $fullPath = Join-Path -Path $basePath -ChildPath $relativePath
    
    $parentDir = Split-Path -Parent $fullPath
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
    }

    $content | Out-File -FilePath $fullPath -Encoding UTF8 -Force
    Write-Host "✅ Archivo creado: $relativePath" -ForegroundColor Green
}

# ==========================================
# 1. DTOs - REQUEST (CON LOMBOK)
# ==========================================

# 1.1 CreatePaylnRequest.java
Write-AppFile "src\main\java\com\tumi\payln\application\dto\request\CreatePaylnRequest.java" 'package com.tumi.payln.application.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;

/**
 * Request para crear una transacción Payln.
 * Usa snake_case según especificación de la prueba.
 */
@Data
@NoArgsConstructor
public class CreatePaylnRequest {
    
    @JsonProperty("client_id")
    @NotBlank(message = "client_id is required")
    private String clientId;
    
    @JsonProperty("account_id")
    @NotBlank(message = "account_id is required")
    private String accountId;
    
    @NotNull(message = "amount is required")
    @DecimalMin(value = "0.01", message = "amount must be greater than 0")
    private BigDecimal amount;
    
    @Pattern(regexp = "COP", message = "Only COP currency is supported")
    private String currency = "COP";
    
    @JsonProperty("payment_method_id")
    @NotBlank(message = "payment_method_id is required")
    private String paymentMethodId;
    
    @JsonProperty("provider_id")
    @NotBlank(message = "provider_id is required")
    private String providerId;
}'

# 1.2 QueryPaylnRequest.java
Write-AppFile "src\main\java\com\tumi\payln\application\dto\request\QueryPaylnRequest.java" 'package com.tumi.payln.application.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Request para consultar una transacción Payln.
 */
@Data
@NoArgsConstructor
public class QueryPaylnRequest {
    
    @JsonProperty("transaction_id")
    @NotBlank(message = "transaction_id is required")
    private String transactionId;
}'

# ==========================================
# 2. DTOs - RESPONSE (CON LOMBOK)
# ==========================================

# 2.1 PaylnResponse.java
Write-AppFile "src\main\java\com\tumi\payln\application\dto\response\PaylnResponse.java" 'package com.tumi.payln.application.dto.response;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Response de una transacción Payln.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PaylnResponse {
    
    @JsonProperty("transaction_id")
    private String transactionId;
    
    @JsonProperty("client_id")
    private String clientId;
    
    @JsonProperty("account_id")
    private String accountId;
    
    private BigDecimal amount;
    private String currency;
    
    @JsonProperty("payment_method_id")
    private String paymentMethodId;
    
    @JsonProperty("provider_id")
    private String providerId;
    
    @JsonProperty("provider_reference")
    private String providerReference;
    
    private String status;
    
    @JsonProperty("status_message")
    private String statusMessage;
    
    @JsonProperty("idempotency_key")
    private String idempotencyKey;
    
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonProperty("created_at")
    private LocalDateTime createdAt;
}'

# 2.2 ErrorResponse.java
Write-AppFile "src\main\java\com\tumi\payln\application\dto\response\ErrorResponse.java" 'package com.tumi.payln.application.dto.response;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * Response para errores de la aplicación.
 */
@Data
@AllArgsConstructor
public class ErrorResponse {
    
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime timestamp;
    
    private int status;
    private String error;
    private String message;
    
    @JsonProperty("path")
    private String requestPath;
    
    public ErrorResponse(int status, String error, String message, String requestPath) {
        this(LocalDateTime.now(), status, error, message, requestPath);
    }
}'

# ==========================================
# 3. PORTS (Interfaces)
# ==========================================

# 3.1 IPaymentProviderPort.java
Write-AppFile "src\main\java\com\tumi\payln\application\port\IPaymentProviderPort.java" 'package com.tumi.payln.application.port;

import com.tumi.payln.domain.model.Amount;
import com.tumi.payln.domain.model.ProviderId;

/**
 * Puerto para integración con proveedores de pago.
 */
public interface IPaymentProviderPort {
    
    /**
     * Procesa un pago con el proveedor especificado.
     * Recibe ValueObjects del dominio para garantizar integridad.
     */
    PaymentResult processPayment(ProviderId providerId, Amount amount, PaymentRequest request);
    
    /**
     * Datos contextuales necesarios para el proveedor (email, cuenta, etc).
     */
    record PaymentRequest(String clientId, String email, String accountNumber) {}
    
    /**
     * Resultado estandarizado del proveedor.
     */
    record PaymentResult(boolean success, String providerReference, String message) {}
}'

# 3.2 IIdempotencyRepositoryPort.java
Write-AppFile "src\main\java\com\tumi\payln\application\port\IIdempotencyRepositoryPort.java" 'package com.tumi.payln.application.port;

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
}'

# 3.3 ICustomerRepositoryPort.java
Write-AppFile "src\main\java\com\tumi\payln\application\port\ICustomerRepositoryPort.java" 'package com.tumi.payln.application.port;

import com.tumi.payln.domain.model.CustomerId;
import java.util.Optional;

/**
 * Puerto para acceso a datos de clientes y cuentas.
 */
public interface ICustomerRepositoryPort {
    
    boolean exists(CustomerId customerId);
    
    boolean accountBelongsToCustomer(CustomerId customerId, String accountId);
    
    boolean isAccountActive(String accountId);
    
    Optional<String> findCustomerEmail(CustomerId customerId);
}'

# 3.4 IProviderCatalogPort.java
Write-AppFile "src\main\java\com\tumi\payln\application\port\IProviderCatalogPort.java" 'package com.tumi.payln.application.port;

import com.tumi.payln.domain.model.ProviderId;

/**
 * Puerto para el catálogo de proveedores.
 */
public interface IProviderCatalogPort {
    
    boolean isProviderActive(ProviderId providerId);
    
    String getProviderName(ProviderId providerId);
}'

# 3.5 IPaymentMethodCatalogPort.java
Write-AppFile "src\main\java\com\tumi\payln\application\port\IPaymentMethodCatalogPort.java" 'package com.tumi.payln.application.port;

import com.tumi.payln.domain.model.PaymentMethodId;

/**
 * Puerto para el catálogo de métodos de pago.
 */
public interface IPaymentMethodCatalogPort {
    
    boolean exists(PaymentMethodId paymentMethodId);
    
    String getPaymentMethodName(PaymentMethodId paymentMethodId);
}'

# ==========================================
# RESUMEN
# ==========================================
Write-Host "`nDTOs y Ports creados exitosamente!" -ForegroundColor Green
Write-Host "`nMejoras Aplicadas:" -ForegroundColor Yellow
Write-Host "   • @JsonFormat: Las fechas ahora se veran como 'yyyy-MM-dd HH:mm:ss'" -ForegroundColor Gray
Write-Host "   • @Pattern: Validacion estricta para moneda COP" -ForegroundColor Gray
Write-Host "   • Ports: Documentacion JavaDoc mejorada" -ForegroundColor Gray
Write-Host "`nProximo paso:" -ForegroundColor Cyan
Write-Host "   Ejecuta el script de los 'Use Cases' (Casos de Uso) para conectar todo." -ForegroundColor White