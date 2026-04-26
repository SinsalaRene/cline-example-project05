import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { FirewallService } from './firewall.service';
import { FirewallRule } from './interfaces';
import { environment } from '../../environments/environment';

describe('FirewallService', () => {
    let service: FirewallService;
    let httpMock: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                FirewallService,
                provideHttpClientTesting()
            ]
        });
        service = TestBed.inject(FirewallService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });

    it('should get all rules', () => {
        const mockResponse = {
            items: [{ id: 1, name: 'Test Rule', status: 'DRAFT' } as FirewallRule],
            total: 1,
            page: 1,
            per_page: 50
        };

        service.getRules().subscribe(rules => {
            expect(rules.total).toBe(1);
            expect(rules.items.length).toBe(1);
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/firewalls/rules`);
        expect(req.request.method).toBe('GET');
        req.flush(mockResponse);
    });

    it('should get a single rule by ID', () => {
        const mockRule: FirewallRule = {
            id: 1,
            name: 'Test Rule',
            description: 'Test',
            landing_zone: 'corp',
            rule_collection_name: 'Collection',
            priority: 100,
            action: 'allow',
            status: 'DRAFT',
            source_address: '0.0.0.0/0',
            destination_address: '10.0.0.0/8',
            destination_ports: ['443'],
            destination_fqdns: ['*.example.com'],
            protocols: ['TCP'],
            category: 'network',
            workload: 'web',
            environment: 'production',
            is_enabled: true
        };

        service.getRuleById(1).subscribe(rule => {
            expect(rule.id).toBe(1);
            expect(rule.name).toBe('Test Rule');
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/firewalls/rules/1`);
        expect(req.request.method).toBe('GET');
        req.flush(mockRule);
    });

    it('should create a new rule', () => {
        const newRule = {
            name: 'New Rule',
            landing_zone: 'corp',
            rule_collection_name: 'Collection',
            priority: 100,
            action: 'allow'
        };

        service.createRule(newRule).subscribe(rule => {
            expect(rule.id).toBe(1);
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/firewalls/rules`);
        expect(req.request.method).toBe('POST');
        expect(req.request.body).toEqual(newRule);
        req.flush({ id: 1 });
    });

    it('should update a rule', () => {
        const updates = { description: 'Updated description' };

        service.updateRule(1, updates).subscribe(rule => {
            expect(rule.description).toBe('Updated description');
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/firewalls/rules/1`);
        expect(req.request.method).toBe('PUT');
        expect(req.request.body).toEqual(updates);
        req.flush({ id: 1, ...newRule, ...updates });
    });

    it('should delete a rule', () => {
        service.deleteRule(1).subscribe(response => {
            expect(response).toBeDefined();
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/firewalls/rules/1`);
        expect(req.request.method).toBe('DELETE');
        req.flush({});
    });

    it('should activate a rule', () => {
        service.activateRule(1).subscribe(rule => {
            expect(rule.status).toBe('ACTIVE');
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/firewalls/rules/1/activate`);
        expect(req.request.method).toBe('POST');
        req.flush({ id: 1, status: 'ACTIVE' });
    });

    it('should filter rules by landing zone', () => {
        service.getRules('corp').subscribe(rules => {
            expect(rules.items.length).toBeGreaterThan(0);
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/firewalls/rules?landing_zone=corp`);
        expect(req.request.method).toBe('GET');
        req.flush({ items: [], total: 0, page: 1, per_page: 50 });
    });

    it('should filter rules by status', () => {
        service.getRules(undefined, 'ACTIVE').subscribe(rules => {
            expect(rules.items.length).toBeGreaterThanOrEqual(0);
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/firewalls/rules?status=ACTIVE`);
        expect(req.request.method).toBe('GET');
        req.flush({ items: [], total: 0, page: 1, per_page: 50 });
    });

    it('should handle HTTP errors', () => {
        let errorReceived = false;
        service.getRules().subscribe(
            () => { },
            () => { errorReceived = true; }
        );

        httpMock.expectOne(`${environment.apiUrl}/firewalls/rules`).flush(null, {
            status: 500,
            statusText: 'Internal Server Error'
        });

        expect(errorReceived).toBe(true);
    });
});