import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

describe('AuthService', () => {
    let service: AuthService;
    let httpMock: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                AuthService,
                provideHttpClientTesting()
            ]
        });
        service = TestBed.inject(AuthService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });

    it('should return true when user is logged in', () => {
        localStorage.setItem('access_token', 'test-token');
        expect(service.isLoggedIn()).toBe(true);
    });

    it('should return false when user is not logged in', () => {
        localStorage.removeItem('access_token');
        expect(service.isLoggedIn()).toBe(false);
    });

    it('should return user info from token', () => {
        localStorage.setItem('access_token', 'test-token');
        const userInfo = service.getUser();
        expect(userInfo).toBeDefined();
    });

    it('should check if user has role', () => {
        localStorage.setItem('access_token', 'test-token');
        const hasRole = service.hasRole('admin');
        expect(hasRole).toBeDefined();
    });

    it('should login and store token', () => {
        const credentials = { email: 'admin@example.com', password: 'password' };

        service.login(credentials.email, credentials.password).subscribe(response => {
            expect(response).toBeDefined();
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
        expect(req.request.method).toBe('POST');
        expect(req.request.body.email).toBe('admin@example.com');
        req.flush({ token: 'new-token' });
    });

    it('should logout and clear token', () => {
        service.logout();
        expect(localStorage.getItem('access_token')).toBeNull();
    });

    it('should handle login failure', () => {
        let errorReceived = false;
        service.login('invalid@example.com', 'wrong-password').subscribe(
            () => { },
            () => { errorReceived = true; }
        );

        httpMock.expectOne(`${environment.apiUrl}/auth/login`).flush(
            { error: 'Invalid credentials' },
            { status: 401, statusText: 'Unauthorized' }
        );

        expect(errorReceived).toBe(true);
    });
});