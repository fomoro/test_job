package com.tumi.payln.domain.service;

import com.tumi.payln.domain.model.PaylnStatus;
import com.tumi.payln.domain.model.PaylnTransaction;

public class PaylnStateMachine {
    
    public void transitionToValidated(PaylnTransaction transaction) {
        // Delega al Aggregate Root
        transaction.markAsValidated();
    }
    
    public void transitionToProcessed(PaylnTransaction transaction, String providerReference) {
        // Delega al Aggregate Root
        transaction.markAsProcessed(providerReference);
    }
    
    public void transitionToFailed(PaylnTransaction transaction, String errorMessage) {
        // Delega al Aggregate Root
        transaction.markAsFailed(errorMessage);
    }
}
