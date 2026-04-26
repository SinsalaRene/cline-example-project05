import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { MatButtonModule } from '@angular/material/button';
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { DashboardComponent } from './dashboard.component';
import { FirewallService } from '../../shared/firewall.service';
import { AuthService } from '../../core/services/auth.service';

describe('DashboardComponent', () => {
    let component: DashboardComponent;
    let fixture: ComponentFixture<DashboardComponent>;
    let firewallServiceSpy: jasmine.SpyObj<FirewallService>;
    let authServiceSpy: jasmine.SpyObj<AuthService>;

    beforeEach(async () => {
        const spyFirewall = jasmine.createSpyObj('FirewallService', ['getRules', 'getStats']);
        const spyAuth = jasmine.createSpyObj('AuthService', ['getUser', 'hasRole', 'isAuthenticated']);

        await TestBed.configureTestingModule({
            imports: [
                DashboardComponent,
                MatButtonModule,
                MatTableModule,
                MatCardModule,
                RouterTestingModule
            ],
            providers: [
                { provide: FirewallService, useValue: spyFirewall },
                { provide: AuthService, useValue: spyAuth }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(DashboardComponent);
        component = fixture.componentInstance;
        firewallServiceSpy = TestBed.inject(FirewallService) as jasmine.SpyObj<FirewallService>;
        authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('should load stats on init', fakeAsync(() => {
        const mockStats = {
            total_rules: 10,
            active_rules: 7,
            draft_rules: 3,
            pending_approvals: 2
        };
        firewallServiceSpy.getStats.and.returnValue(of(mockStats));

        component.ngOnInit();
        tick();

        expect(component.stats).toEqual(mockStats);
        expect(firewallServiceSpy.getStats).toHaveBeenCalled();
    }));

    it('should display dashboard statistics', fakeAsync(() => {
        const mockStats = {
            total_rules: 10,
            active_rules: 7,
            draft_rules: 3,
            pending_approvals: 2
        };
        firewallServiceSpy.getStats.and.returnValue(of(mockStats));

        component.ngOnInit();
        tick();

        const compiled = fixture.nativeElement as HTMLElement;
        const statValues = compiled.querySelectorAll('.stat-value');
        expect(statValues.length).toBeGreaterThan(0);
    }));

    it('should refresh stats on refresh action', fakeAsync(() => {
        const mockStats = {
            total_rules: 5,
            active_rules: 3,
            draft_rules: 2,
            pending_approvals: 1
        };
        firewallServiceSpy.getStats.and.returnValue(of(mockStats));

        component.refreshStats();
        tick();

        expect(component.stats).toEqual(mockStats);
        expect(firewallServiceSpy.getStats).toHaveBeenCalled();
    }));

    it('should handle loading state', fakeAsync(() => {
        firewallServiceSpy.getStats.and.returnValue(of(null));

        component.isLoading = true;
        fixture.detectChanges();
        tick();

        const compiled = fixture.nativeElement as HTMLElement;
        const spinner = compiled.querySelector('.loading-spinner');
        expect(spinner).toBeTruthy();
    }));

    it('should display error message on failed API call', fakeAsync(() => {
        firewallServiceSpy.getStats.and.returnValue(throwError(new Error('API Error')));

        component.ngOnInit();
        tick();

        expect(component.errorMessage).toBeDefined();
    }));

    it('should have correct role check', () => {
        authServiceSpy.isAuthenticated.and.returnValue(true);
        authServiceSpy.hasRole.and.returnValue(['admin', 'security_stakeholder']);

        expect(component.canManage()).toBe(true);
    });
});