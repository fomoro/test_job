# ==========================================
# 14_infra_rest.ps1
# CREACIÓN DE ADAPTADORES REST (Controllers, DTOs, Handlers)
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Creando REST Layer en: $basePath" -ForegroundColor Cyan

function Write-InfraFile {
    param ([string]$relativePath, [string]$content)
    $fullPath = Join-Path -Path $basePath -ChildPath $relativePath
    $parentDir = Split-Path -Parent $fullPath
    if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Force -Path $parentDir | Out-Null }
    $content | Out-File -FilePath $fullPath -Encoding UTF8 -Force
    Write-Host "✅ Archivo creado: $relativePath" -ForegroundColor Green
}

# ==========================================
# 1. DTOs REST
# ==========================================

# 1.1 PaylnRestRequest.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\adapter\rest\dto\PaylnRestRequest.java" 'package com.tumi.payln.infrastructure.adapter.rest.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.math.BigDecimal;

@Data
@NoArgsConstructor
public class PaylnRestRequest {
    
    @JsonProperty("client_id")
    @NotBlank(message = "client_id is required")
    private String clientId;
    
    @JsonProperty("account_id")
    @NotBlank(message = "account_id is required")
    private String accountId;
    
    @NotNull(message = "amount is required")
    @DecimalMin(value = "0.01", message = "amount must be greater than 0")
    private BigDecimal amount;
    
    private String currency = "COP";
    
    @JsonProperty("payment_method_id")
    @NotBlank(message = "payment_method_id is required")
    private String paymentMethodId;
    
    @JsonProperty("provider_id")
    @NotBlank(message = "provider_id is required")
    private String providerId;
}'

# 1.2 PaylnRestResponse.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\adapter\rest\dto\PaylnRestResponse.java" 'package com.tumi.payln.infrastructure.adapter.rest.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PaylnRestResponse {
    
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

# ==========================================
# 2. HANDLER (Manejo de Errores)
# ==========================================

# 2.1 GlobalExceptionHandler.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\adapter\rest\handler\GlobalExceptionHandler.java" 'package com.tumi.payln.infrastructure.adapter.rest.handler;

import com.tumi.payln.application.dto.response.ErrorResponse;
import com.tumi.payln.application.exception.ApplicationException;
import com.tumi.payln.application.exception.BusinessRuleException;
import com.tumi.payln.application.exception.ValidationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;
import jakarta.servlet.http.HttpServletRequest;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(ValidationException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(ValidationException ex, WebRequest request) {
        return buildResponse(HttpStatus.BAD_REQUEST, "Validation Error", ex.getMessage(), request);
    }
    
    @ExceptionHandler(BusinessRuleException.class)
    public ResponseEntity<ErrorResponse> handleBusinessRuleException(BusinessRuleException ex, WebRequest request) {
        return buildResponse(HttpStatus.CONFLICT, "Business Rule Violation", ex.getMessage(), request);
    }
    
    @ExceptionHandler(ApplicationException.class)
    public ResponseEntity<ErrorResponse> handleApplicationException(ApplicationException ex, WebRequest request) {
        log.error("Application error: ", ex);
        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "Application Error", ex.getMessage(), request);
    }
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidationExceptions(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getAllErrors().forEach((error) -> {
            String fieldName = ((FieldError) error).getField();
            String errorMessage = error.getDefaultMessage();
            errors.put(fieldName, errorMessage);
        });
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(errors);
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex, WebRequest request) {
        log.error("Unhandled error: ", ex);
        return buildResponse(HttpStatus.INTERNAL_SERVER_ERROR, "Internal Server Error", "An unexpected error occurred", request);
    }
    
    private ResponseEntity<ErrorResponse> buildResponse(HttpStatus status, String error, String message, WebRequest request) {
        String path = (request instanceof ServletWebRequest) ? ((ServletWebRequest) request).getRequest().getRequestURI() : "unknown";
        ErrorResponse errorResponse = new ErrorResponse(status.value(), error, message, path);
        return ResponseEntity.status(status).body(errorResponse);
    }
}'

# ==========================================
# 3. CONTROLLERS
# ==========================================

# 3.1 PaylnController.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\adapter\rest\controller\PaylnController.java" 'package com.tumi.payln.infrastructure.adapter.rest.controller;

import com.tumi.payln.application.dto.request.CreatePaylnRequest;
import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.service.ProcessPaylnUseCase;
import com.tumi.payln.infrastructure.adapter.rest.dto.PaylnRestRequest;
import com.tumi.payln.infrastructure.adapter.rest.dto.PaylnRestResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.UUID;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/payins")
public class PaylnController {
    
    private final ProcessPaylnUseCase processPaylnUseCase;
    
    @PostMapping
    public ResponseEntity<PaylnRestResponse> createPayln(
            @Valid @RequestBody PaylnRestRequest restRequest,
            @RequestHeader(value = "x-idempotency-key", required = false) String idempotencyKey) {
        
        log.info("Received Payln request: client={}", restRequest.getClientId());
        
        String finalIdempotencyKey = (idempotencyKey != null && !idempotencyKey.isBlank()) 
            ? idempotencyKey 
            : "key-" + UUID.randomUUID().toString();
        
        CreatePaylnRequest appRequest = new CreatePaylnRequest();
        appRequest.setClientId(restRequest.getClientId());
        appRequest.setAccountId(restRequest.getAccountId());
        appRequest.setAmount(restRequest.getAmount());
        appRequest.setCurrency(restRequest.getCurrency());
        appRequest.setPaymentMethodId(restRequest.getPaymentMethodId());
        appRequest.setProviderId(restRequest.getProviderId());
        
        PaylnResponse appResponse = processPaylnUseCase.execute(appRequest, finalIdempotencyKey);
        
        return ResponseEntity.status(HttpStatus.CREATED)
                .header("x-idempotency-key", finalIdempotencyKey)
                .body(mapToRestResponse(appResponse));
    }
    
    private PaylnRestResponse mapToRestResponse(PaylnResponse r) {
        return new PaylnRestResponse(
            r.getTransactionId(), r.getClientId(), r.getAccountId(), r.getAmount(),
            r.getCurrency(), r.getPaymentMethodId(), r.getProviderId(), r.getProviderReference(),
            r.getStatus(), r.getStatusMessage(), r.getIdempotencyKey(), r.getCreatedAt()
        );
    }
}'

# 3.2 PaylnQueryController.java
Write-InfraFile "src\main\java\com\tumi\payln\infrastructure\adapter\rest\controller\PaylnQueryController.java" 'package com.tumi.payln.infrastructure.adapter.rest.controller;

import com.tumi.payln.application.dto.request.QueryPaylnRequest;
import com.tumi.payln.application.dto.response.PaylnResponse;
import com.tumi.payln.application.service.QueryPaylnUseCase;
import com.tumi.payln.infrastructure.adapter.rest.dto.PaylnRestResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/payins")
public class PaylnQueryController {
    
    private final QueryPaylnUseCase queryPaylnUseCase;
    
    @GetMapping("/{transaction_id}")
    public ResponseEntity<PaylnRestResponse> getPayln(@PathVariable("transaction_id") String transactionId) {
        
        QueryPaylnRequest request = new QueryPaylnRequest();
        request.setTransactionId(transactionId);
        
        PaylnResponse r = queryPaylnUseCase.execute(request);
        
        PaylnRestResponse response = new PaylnRestResponse(
            r.getTransactionId(), r.getClientId(), r.getAccountId(), r.getAmount(),
            r.getCurrency(), r.getPaymentMethodId(), r.getProviderId(), r.getProviderReference(),
            r.getStatus(), r.getStatusMessage(), r.getIdempotencyKey(), r.getCreatedAt()
        );
        
        return ResponseEntity.ok(response);
    }
}'

Write-Host "✅ REST Adapters generados correctamente." -ForegroundColor Green