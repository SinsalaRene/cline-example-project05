import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Observable } from 'rxjs';

import { RequestInterceptor } from './request.interceptor';
import { AuthService } from '../services/auth.service';
import { environment } from '../../../environments/environment';

describe('RequestInterceptor', () => {
    let httpMock: HttpTestingController;
    let authService: jasmine.SpyObj<AuthService>;
    let interceptor: RequestInterceptor;

    beforeEach(() => {
        const spyAuthService = jasmine.createSpyObj('AuthService', ['getToken']);

        TestBed.configureTestingModule({
            providers: [
                RequestInterceptor,
                provideHttpClientTesting(),
                { provide: AuthService, useValue: spyAuthService }
            ]
        });

        interceptor = TestBed.inject(RequestInterceptor);
        httpMock = TestBed.inject(HttpTestingController);
        authService = TestBed.inject(AuthService) as jasmine.SpyObj<AuthService>;
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(interceptor).toBeTruthy();
    });

    it('should add Authorization header with token', () => {
        authService.getToken.and.returnValue('test-token');

        const req = new HttpRequest('GET', `${environment.apiUrl}/rules`);
        const cloned = interceptor.intercept(req, {
            handle: (req: HttpRequest<any>): Observable<HttpEvent<any>> => {
                expect(req.headers.get('Authorization')).toBe('Bearer test-token');
                return new Observable<HttpEvent<any>>();
            }
        });

        // Trigger the observable
        cloned.subscribe();
        httpMock.expectNone(`${environment.apiUrl}/rules`);
    });

    it('should not add auth header for non-API requests', () => {
        authService.getToken.and.returnValue('test-token');

        const req = new HttpRequest('GET', 'http://example.com/non-api');
        const cloned = interceptor.intercept(req, {
            handle: (req: HttpRequest<any>): Observable<HttpEvent<any>> => {
                expect(req.headers.get('Authorization')).toBeNull();
                return new Observable<HttpEvent<any>>();
            }
        });

        cloned.subscribe();
        httpMock.expectNone(`${environment.apiUrl}/non-api`);
    });

    it('should handle missing token gracefully', () => {
        authService.getToken.and.returnValue(null);

        const req = new HttpRequest('GET', `${environment.apiUrl}/rules`);
        const cloned = interceptor.intercept(req, {
            handle: (req: HttpRequest<any>): Observable<HttpEvent<any>> => {
                expect(req.headers.get('Authorization')).toBeNull();
                return new Observable<HttpEvent<any>>();
            }
        });

        cloned.subscribe();
        httpMock.expectNone(`${environment.apiUrl}/rules`);
    });
});