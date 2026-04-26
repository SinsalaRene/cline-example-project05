/// <reference types="cypress" />

declare global {
    // eslint-disable-next-line no-unused-vars
    namespace Cypress {
        // eslint-disable-next-line no-unused-vars
        interface Chainable {
            login(email: string, password: string): void;
            waitForApi(method: string, url: string): void;
        }
    }
}

Cypress.Commands.add('login', (email: string, password: string) => {
    cy.session(email, () => {
        cy.visit('/login');
        cy.get('input[placeholder="Email"], input[type="email"]').clear().type(email);
        cy.get('input[placeholder="Password"], input[type="password"]').clear().type(password);
        cy.get('button[type="submit"], button:contains("Login")').click();
        cy.url().should('not.include', '/login');
    });
});

Cypress.Commands.add('waitForApi', (method: string, url: string) => {
    cy.intercept(method, url).as('apiRequest');
    return cy.get('@apiRequest');
});