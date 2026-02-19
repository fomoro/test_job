package com.tumi.payln.infrastructure.config;

import com.tumi.payln.domain.service.IdempotencyService;
import com.tumi.payln.domain.service.PaylnStateMachine;
import com.tumi.payln.domain.service.PaylnValidator;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * CONFIGURACIÃƒÆ’Ã†â€™Ãƒâ€ Ã¢â‚¬â„¢ÃƒÆ’Ã¢â‚¬Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡Ãƒâ€šÃ‚Â¬ÃƒÆ’Ã¢â‚¬Â¦ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œN DE DOMINIO
 * * Registra los servicios de dominio puros como Beans de Spring.
 * Esto mantiene el paquete "domain" libre de dependencias del framework (Clean Architecture).
 */
@Configuration
public class DomainConfig {

    @Bean
    public PaylnValidator paylnValidator() {
        return new PaylnValidator();
    }

    @Bean
    public PaylnStateMachine paylnStateMachine() {
        return new PaylnStateMachine();
    }

    @Bean
    public IdempotencyService idempotencyService() {
        return new IdempotencyService();
    }
}
