import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';
import { FirewallService } from '../../shared/firewall.service';
import { AuthService } from '../../core/services/auth.service';

import { RulesComponent } from './rules.component';

describe('RulesComponent', () => {
    let component: RulesComponent;
    let fixture: ComponentFixture<RulesComponent>;
    let firewallServiceSpy: jasmine.SpyObj<FirewallService>;
    let authServiceSpy: jasmine.SpyObj<AuthService>;

    beforeEach(async () => {
        const spyFirewall = jasmine.createSpyObj('FirewallService', ['getRules', 'deleteRule', 'createRule', 'updateRule']);
        const spyAuth = jasmine.createSpyObj('AuthService', ['getUser', 'hasRole']);

        await TestBed.configureTestingModule({
            imports: [
                RulesComponent,
                MatButtonModule,
                MatTableModule,
                MatPaginatorModule,
                MatSortModule,
                MatInputModule,
                MatFormFieldModule,
                MatCardModule,
                MatIconModule,
                RouterTestingModule
            ],
            providers: [
                { provide: FirewallService, useValue: spyFirewall },
                { provide: AuthService, useValue: spyAuth }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(RulesComponent);
        component = fixture.componentInstance;
        firewallServiceSpy = TestBed.inject(FirewallService) as jasmine.SpyObj<FirewallService>;
        authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('should load rules on init', fakeAsync(() => {
        const mockResponse = {
            items: [
                { id: 1, name: 'Rule 1', status: 'DRAFT' },
                { id: 2, name: 'Rule 2', status: 'ACTIVE' }
            ],
            total: 2,
            page: 1,
            per_page: 50
        };
        firewallServiceSpy.getRules.and.returnValue(of(mockResponse));

        fixture.detectChanges();
        tick();

        expect(component.rules).toEqual(mockResponse.items);
        expect(firewallServiceSpy.getRules).toHaveBeenCalled();
    }));

    it('should display rule count', fakeAsync(() => {
        const mockResponse = {
            items: [{ id: 1, name: 'Rule 1', status: 'DRAFT' }],
            total: 1,
            page: 1,
            per_page: 50
        };
        firewallServiceSpy.getRules.and.returnValue(of(mockResponse));

        fixture.detectChanges();
        tick();

        expect(component.totalRules).toBe(1);
    }));

    it('should handle error when loading rules', fakeAsync(() => {
        firewallServiceSpy.getRules.and.returnValue(throwError(() => new Error('Network error')));

        fixture.detectChanges();
        tick();

        expect(component.error).toBeDefined();
    }));

    it('should filter rules by search term', fakeAsync(() => {
        const mockRules = [
            { id: 1, name: 'Allow HTTPS', status: 'ACTIVE' },
            { id: 2, name: 'Deny SSH', status: 'DRAFT' },
            { id: 3, name: 'Allow HTTP', status: 'ACTIVE' }
        ];
        const mockResponse = { items: mockRules, total: 3, page: 1, per_page: 50 };
        firewallServiceSpy.getRules.and.returnValue(of(mockResponse));

        component.searchTerm = 'Allow';
        component.applyFilters();
        fixture.detectChanges();
        tick();

        expect(component.filteredRules!.length).toBe(2);
    }));

    it('should filter rules by status', fakeAsync(() => {
        const mockRules = [
            { id: 1, name: 'Rule 1', status: 'ACTIVE' },
            { id: 2, name: 'Rule 2', status: 'DRAFT' }
        ];
        const mockResponse = { items: mockRules, total: 2, page: 1, per_page: 50 };
        firewallServiceSpy.getRules.and.returnValue(of(mockResponse));

        component.statusFilter = 'ACTIVE';
        component.applyFilters();
        fixture.detectChanges();
        tick();

        expect(component.filteredRules!.length).toBe(1);
    }));

    it('should navigate to rule detail', fakeAsync(() => {
        const mockResponse = {
            items: [{ id: 1, name: 'Rule 1', status: 'DRAFT' }],
            total: 1,
            page: 1,
            per_page: 50
        };
        firewallServiceSpy.getRules.and.returnValue(of(mockResponse));

        fixture.detectChanges();
        tick();

        component.viewRule(mockResponse.items[0]);
        // Navigation would be tested with RouterTestingModule
        expect(component.selectedRuleId).toBe(1);
    }));

    it('should delete a rule', fakeAsync(() => {
        const mockResponse = {
            items: [{ id: 1, name: 'Rule 1', status: 'DRAFT' }],
            total: 1,
            page: 1,
            per_page: 50
        };
        firewallServiceSpy.getRules.and.returnValue(of(mockResponse));
        firewallServiceSpy.deleteRule.and.returnValue(of({}));

        fixture.detectChanges();
        tick();

        component.deleteRule(mockResponse.items[0]);
        expect(firewallServiceSpy.deleteRule).toHaveBeenCalledWith(1);
    }));

    it('should create a new rule', fakeAsync(() => {
        firewallServiceSpy.createRule.and.returnValue(of({ id: 10, name: 'New Rule', status: 'DRAFT' }));

        component.newRule = {
            name: 'New Rule',
            landing_zone: 'corp',
            rule_collection_name: 'Collection',
            priority: 100,
            action: 'allow'
        } as any;

        component.createRule();
        expect(firewallServiceSpy.createRule).toHaveBeenCalledWith(jasmine.objectContaining({
            name: 'New Rule'
        }));
    }));

    it('should have active rules count', () => {
        component.rules = [
            { id: 1, name: 'Rule 1', status: 'ACTIVE' },
            { id: 2, name: 'Rule 2', status: 'DRAFT' }
        ];
        expect(component.activeRulesCount).toBe(1);
    });

    it('should have draft rules count', () => {
        component.rules = [
            { id: 1, name: 'Rule 1', status: 'ACTIVE' },
            { id: 2, name: 'Rule 2', status: 'DRAFT' }
        ];
        expect(component.draftRulesCount).toBe(1);
    });
});