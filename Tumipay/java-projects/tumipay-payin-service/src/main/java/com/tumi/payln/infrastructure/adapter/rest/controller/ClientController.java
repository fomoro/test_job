package com.tumi.payln.infrastructure.adapter.rest.controller;

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
}
