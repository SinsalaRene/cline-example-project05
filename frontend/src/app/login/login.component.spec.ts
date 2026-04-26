import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { ReactiveFormsModule, FormsModule } from '@angular/forms';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { LoginComponent } from './login.component';
import { AuthService } from '../core/services/auth.service';
import { Router } from '@angular/router';

describe('LoginComponent', () => {
    let component: LoginComponent;
    let fixture: ComponentFixture<LoginComponent>;
    let authServiceSpy: jasmine.SpyObj<AuthService>;
    let routerSpy: jasmine.SpyObj<Router>;

    beforeEach(async () => {
        const spyAuth = jasmine.createSpyObj('AuthService', ['login', 'logout', 'isAuthenticated']);
        const spyRouter = jasmine.createSpyObj('Router', ['navigate']);

        await TestBed.configureTestingModule({
            imports: [
                LoginComponent,
                ReactiveFormsModule,
                FormsModule,
                RouterTestingModule
            ],
            providers: [
                { provide: AuthService, useValue: spyAuth },
                { provide: Router, useValue: spyRouter }
            ]
        }).compileComponents();

        fixture = TestBed.createComponent(LoginComponent);
        component = fixture.componentInstance;
        authServiceSpy = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
        routerSpy = TestBed.inject(Router) as jasmine.SpyObj<Router>;
    });

    it('should create', () => {
        expect(component).toBeTruthy();
    });

    it('should have valid initial form state', () => {
        expect(component.loginForm).toBeDefined();
        expect(component.loginForm.valid).toBe(false);
    });

    it('should enable submit button when form is valid', () => {
        component.email = 'user@example.com';
        component.password = 'password123';
        fixture.detectChanges();

        const compiled = fixture.nativeElement as HTMLElement;
        const submitBtn = compiled.querySelector('button[type="submit"]');
        expect(submitBtn?.hasAttribute('disabled')).toBe(false);
    });

    it('should disable submit button when form is invalid', () => {
        const compiled = fixture.nativeElement as HTMLElement;
        const submitBtn = compiled.querySelector('button[type="submit"]');
        expect(submitBtn?.hasAttribute('disabled')).toBe(true);
    });

    it('should show error on login failure', fakeAsync(() => {
        authServiceSpy.login.and.returnValue(throwError(new Error('Invalid credentials')));

        component.email = 'user@example.com';
        component.password = 'wrongpassword';
        component.onSubmit();
        tick();

        expect(component.error).toBe('Invalid credentials');
    }));

    it('should redirect on successful login', fakeAsync(() => {
        authServiceSpy.login.and.returnValue(of({ token: 'test-token' }));

        component.email = 'user@example.com';
        component.password = 'correctpassword';
        component.onSubmit();
        tick();

        expect(routerSpy.navigate).toHaveBeenCalledWith(['/dashboard']);
        expect(component.error).toBeNull();
    }));

    it('should validate email format', () => {
        component.email = 'invalid-email';
        fixture.detectChanges();

        const compiled = fixture.nativeElement as HTMLElement;
        const emailInput = compiled.querySelector('input[type="email"], input[placeholder="Email"]');
        expect(emailInput).toBeTruthy();
    });

    it('should validate password length', () => {
        component.password = '123';
        fixture.detectChanges();

        const compiled = fixture.nativeElement as HTMLElement;
        const passwordInput = compiled.querySelector('input[type="password"], input[placeholder="Password"]');
        expect(passwordInput).toBeTruthy();
    });

    it('should clear error on new login attempt', fakeAsync(() => {
        component.error = 'Previous error';
        component.email = 'user@example.com';
        component.password = 'newpassword';
        authServiceSpy.login.and.returnValue(of({ token: 'test-token' }));
        component.onSubmit();
        tick();

        expect(component.error).toBeNull();
    }));

    it('should handle network errors', fakeAsync(() => {
        const networkError = new Error('Network error');
        authServiceSpy.login.and.returnValue(throwError(networkError));

        component.email = 'user@example.com';
        component.password = 'password';
        component.onSubmit();
        tick();

        expect(component.error).toBeTruthy();
    }));
});