{
    "name": "fw-portal-e2e",
        "version": "1.0.0",
            "description": "End-to-end tests for Firewall Portal",
                "scripts": {
        "e2e": "cypress open",
            "e2e:headless": "cypress run",
                "cy:verify": "cypress verify",
                    "cy:update": "cypress update"
    },
    "dependencies": {
        "cypress": "^13.0.0"
    },
    "devDependencies": {
        "@types/cypress": "^2.3.1"
    }
}