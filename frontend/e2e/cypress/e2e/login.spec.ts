describe('Login Flow', () => {
    beforeEach(() => {
        cy.visit('/login');
    });

    afterEach(() => {
        cy.clearCookies();
        cy.clearLocalStorage();
    });

    it('should display login page', () => {
        cy.get('h1').should('contain', 'Login');
        cy.get('input[placeholder="Email"], input[type="email"]').should('be.visible');
        cy.get('input[placeholder="Password"], input[type="password"]').should('be.visible');
        cy.get('button[type="submit"], button:contains("Login")').should('contain', 'Login');
    });

    it('should show error for invalid credentials', () => {
        cy.get('input[placeholder="Email"], input[type="email"]').type('invalid@example.com');
        cy.get('input[placeholder="Password"], input[type="password"]').type('wrongpassword');
        cy.get('button[type="submit"], button:contains("Login")').click();

        cy.get('.error-message, .mat-error').should('be.visible');
    });

    it('should enable submit button when form is valid', () => {
        cy.get('input[placeholder="Email"], input[type="email"]').type('user@example.com');
        cy.get('input[placeholder="Password"], input[type="password"]').type('password123');

        cy.get('button[type="submit"]').should('not.be.disabled');
    });

    it('should disable submit button when form is invalid', () => {
        cy.get('button[type="submit"]').should('be.disabled');
    });

    it('should display form validation messages', () => {
        cy.get('button[type="submit"], button:contains("Login")').click();

        cy.get('mat-error, .error-message').should('contain', 'required');
    });
});