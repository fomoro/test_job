package com.tumi.payln.infrastructure.adapter.rest.dto;

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
}
