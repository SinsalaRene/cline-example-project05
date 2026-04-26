import { defineConfig } from "cypress";

export default defineConfig({
    e2e: {
        baseUrl: 'http://localhost:4200',
        supportFile: 'cypress/support/e2e.ts',
        defaultCommandTimeout: 10000,
        viewport: { width: 1280, height: 720 },
        video: false,
        screenshotOnRunFailure: true,
        retries: {
            runMode: 2,
            openMode: 0,
        },
    },
    component: {
        spec: 'cypress/e2e/**/*.cy.ts',
    },
});