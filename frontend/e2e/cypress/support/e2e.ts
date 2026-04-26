import './commands';

// Global error handler
Cypress.on('uncaught:exception', (err, runnable) => {
    // returning false here prevents Cypress from failing the test on uncaught exceptions
    if (err.message.includes('ResizeObserver')) {
        return false;
    }
    return true;
});