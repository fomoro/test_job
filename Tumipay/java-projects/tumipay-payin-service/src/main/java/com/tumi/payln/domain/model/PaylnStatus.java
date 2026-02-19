package com.tumi.payln.domain.model;

public enum PaylnStatus {
    CREATED,
    VALIDATED,
    PROCESSED,
    FAILED;
    
    public boolean isTerminal() {
        return this == PROCESSED || this == FAILED;
    }
}
