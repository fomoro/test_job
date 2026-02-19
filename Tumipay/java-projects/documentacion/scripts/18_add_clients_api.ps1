# ==========================================
# 18_add_clients_api.ps1
# AGREGAR ENDPOINT GET /api/v1/clients
# ==========================================
$basePath = "C:\source\test\code\Nueva carpeta\Tumipay\java-projects\tumipay-payin-service"

Write-Host "Agregando API de Clientes en: $basePath" -ForegroundColor Cyan

function Write-File {
    param ([string]$relativePath, [string]$content)
    $fullPath = Join-Path -Path $basePath -ChildPath $relativePath
    $parentDir = Split-Path -Parent $fullPath
    if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Force -Path $parentDir | Out-Null }
    $content | Out-File -FilePath $fullPath -Encoding UTF8 -Force
    Write-Host "✅ Archivo actualizado/creado: $relativePath" -ForegroundColor Green
}

# 1. DOMINIO: Modelo Customer
Write-File "src\main\java\com\tumi\payln\domain\model\Customer.java" 'package com.tumi.payln.domain.model;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.Builder;

@Getter
@Builder
@AllArgsConstructor
public class Customer {
    private final CustomerId id;
    private final String fullName;
    private final String email;
}'

# 2. PUERTO: Actualizar ICustomerRepositoryPort (Sobreescribimos para añadir findAll)
Write-File "src\main\java\com\tumi\payln\application\port\ICustomerRepositoryPort.java" 'package com.tumi.payln.application.port;

import com.tumi.payln.domain.model.Customer;
import com.tumi.payln.domain.model.CustomerId;
import java.util.List;
import java.util.Optional;

public interface ICustomerRepositoryPort {
    
    boolean exists(CustomerId customerId);
    
    boolean accountBelongsToCustomer(CustomerId customerId, String accountId);
    
    boolean isAccountActive(String accountId);
    
    Optional<String> findCustomerEmail(CustomerId customerId);

    // NUEVO MÉTODO
    List<Customer> findAll();
}'

# 3. ADAPTADOR: Actualizar CustomerRepositoryAdapter (Implementar findAll)
Write-File "src\main\java\com\tumi\payln\infrastructure\adapter\persistence\CustomerRepositoryAdapter.java" 'package com.tumi.payln.infrastructure.adapter.persistence;

import com.tumi.payln.application.port.ICustomerRepositoryPort;
import com.tumi.payln.domain.model.Customer;
import com.tumi.payln.domain.model.CustomerId;
import com.tumi.payln.infrastructure.persistence.entity.CustomerEntity;
import com.tumi.payln.infrastructure.persistence.repository.JpaCustomerRepository;
import com.tumi.payln.infrastructure.persistence.repository.JpaAccountRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Slf4j
@Component
@RequiredArgsConstructor
public class CustomerRepositoryAdapter implements ICustomerRepositoryPort {
    
    private final JpaCustomerRepository jpaCustomerRepository;
    private final JpaAccountRepository jpaAccountRepository;
    
    @Override
    public boolean exists(CustomerId customerId) {
        return jpaCustomerRepository.existsById(customerId.value());
    }
    
    @Override
    public boolean accountBelongsToCustomer(CustomerId customerId, String accountId) {
        return jpaCustomerRepository.existsAccountForCustomer(customerId.value(), accountId);
    }
    
    @Override
    public boolean isAccountActive(String accountId) {
        return jpaAccountRepository.findStatusByAccountId(accountId)
            .map(status -> "active".equalsIgnoreCase(status))
            .orElse(false);
    }
    
    @Override
    public Optional<String> findCustomerEmail(CustomerId customerId) {
        return jpaCustomerRepository.findById(customerId.value())
            .map(CustomerEntity::getEmail);
    }

    @Override
    public List<Customer> findAll() {
        return jpaCustomerRepository.findAll().stream()
            .map(entity -> Customer.builder()
                .id(new CustomerId(entity.getClientId()))
                .fullName(entity.getFullName())
                .email(entity.getEmail())
                .build())
            .collect(Collectors.toList());
    }
}'

# 4. APLICACIÓN: ListClientsUseCase
Write-File "src\main\java\com\tumi\payln\application\service\ListClientsUseCase.java" 'package com.tumi.payln.application.service;

import com.tumi.payln.application.port.ICustomerRepositoryPort;
import com.tumi.payln.domain.model.Customer;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ListClientsUseCase {
    
    private final ICustomerRepositoryPort customerRepository;
    
    public List<Customer> execute() {
        return customerRepository.findAll();
    }
}'

# 5. INFRAESTRUCTURA: ClientRestResponse (DTO)
Write-File "src\main\java\com\tumi\payln\infrastructure\adapter\rest\dto\ClientRestResponse.java" 'package com.tumi.payln.infrastructure.adapter.rest.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class ClientRestResponse {
    @JsonProperty("client_id")
    private String clientId;
    
    @JsonProperty("full_name")
    private String fullName;
    
    private String email;
}'

# 6. INFRAESTRUCTURA: ClientController
Write-File "src\main\java\com\tumi\payln\infrastructure\adapter\rest\controller\ClientController.java" 'package com.tumi.payln.infrastructure.adapter.rest.controller;

import com.tumi.payln.application.service.ListClientsUseCase;
import com.tumi.payln.infrastructure.adapter.rest.dto.ClientRestResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/clients")
@RequiredArgsConstructor
public class ClientController {

    private final ListClientsUseCase listClientsUseCase;

    @GetMapping
    public ResponseEntity<List<ClientRestResponse>> listClients() {
        List<ClientRestResponse> response = listClientsUseCase.execute().stream()
            .map(c -> new ClientRestResponse(c.getId().value(), c.getFullName(), c.getEmail()))
            .collect(Collectors.toList());
            
        return ResponseEntity.ok(response);
    }
}'

Write-Host "`n✅ API de Clientes implementada." -ForegroundColor Yellow
Write-Host "1. Ejecuta el script de limpieza BOM (17_fix_bom.ps1) por si acaso." -ForegroundColor Gray
Write-Host "2. Ejecuta: mvn spring-boot:run" -ForegroundColor White