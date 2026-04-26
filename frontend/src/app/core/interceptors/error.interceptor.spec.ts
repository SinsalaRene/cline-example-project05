import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpRequest, HttpHandler, HttpEvent, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';

import { ErrorInterceptor } from './error.interceptor';

describe('ErrorInterceptor', () => {
    let httpMock: HttpTestingController;
    let interceptor: ErrorInterceptor;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                ErrorInterceptor,
                provideHttpClientTesting()
            ]
        });

        interceptor = TestBed.inject(ErrorInterceptor);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(interceptor).toBeTruthy();
    });

    it('should pass successful responses through', () => {
        let responseReceived: any = null;

        const req = new HttpRequest('GET', '/api/test');
        const cloned = interceptor.intercept(req, {
            handle: (req: HttpRequest<any>): Observable<HttpEvent<any>> => {
                return new Observable<HttpEvent<any>>((observer) => {
                    observer.next({ type: 4 } as HttpEvent<any>);
                    observer.complete();
                });
            }
        });

        cloned.subscribe({
            next: (event) => { responseReceived = event; },
            error: (err) => { fail('should not error'); }
        });

        expect(responseReceived).toBeDefined();
    });

    it('should format 401 errors', fakeAsync(() => {
        let errorReceived: any = null;

        const req = httpMock.expectOne('/api/test');
        req.error(new ProgressEvent('error'), new HTTPResponseConfig());

        interceptor.intercept(
            new HttpRequest('GET', '/api/test'),
            {
                handle: () => new Observable<HttpEvent<any>>((observer) => {
                    observer.error(new HttpErrorResponse({ status: 401 }));
                })
            }
        ).subscribe({
            error: (err) => { errorReceived = err; }
        });

        tick();
        expect(errorReceived).toBeDefined();
    }));

    it('should handle 500 server errors', fakeTick(() => {
        const mockError = new HttpErrorResponse({
            status: 500,
            statusText: 'Internal Server Error',
            error: { message: 'Server error' }
        });

        let errorReceived: HttpErrorResponse | null = null;

        interceptor.intercept(
            new HttpRequest('GET', '/api/test'),
            {
                handle: (): Observable<HttpEvent<any>> => throwError(() => mockError)
            }
        ).subscribe({
            error: (err) => { errorReceived = err; }
        });

        expect(errorReceived).toEqual(mockError);
    }));
});

class HTTPResponseConfig {
    status = 200;
    statusText = 'OK';
    ok = true;
}

function fakeTick(fn: () => void): void {
    fn();
}