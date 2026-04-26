import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ApiService } from './api.service';
import { environment } from '../../environments/environment';

describe('ApiService', () => {
    let service: ApiService;
    let httpMock: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                ApiService,
                provideHttpClientTesting()
            ]
        });
        service = TestBed.inject(ApiService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });

    it('should make GET request', fakeAsync(() => {
        const mockData = [{ id: 1, name: 'Test Rule' }];
        service.get('/rules').subscribe(rules => {
            expect(rules).toEqual(mockData);
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/rules`);
        expect(req.request.method).toBe('GET');
        req.flush(mockData);
        tick();
    }));

    it('should make POST request with auth header', fakeAsync(() => {
        localStorage.setItem('access_token', 'test-token');
        const postData = { name: 'New Rule' };
        service.post('/rules', postData).subscribe(result => {
            expect(result).toEqual({ id: 1 });
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/rules`);
        expect(req.request.method).toBe('POST');
        expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
        req.flush({ id: 1 });
        tick();
    }));

    it('should make PUT request', fakeAsync(() => {
        const updateData = { description: 'Updated' };
        service.put('/rules/1', updateData).subscribe();

        const req = httpMock.expectOne(`${environment.apiUrl}/rules/1`);
        expect(req.request.method).toBe('PUT');
        expect(req.request.body).toEqual(updateData);
        req.flush({ id: 1 });
        tick();
    }));

    it('should make DELETE request', fakeAsync(() => {
        service.delete('/rules/1').subscribe();

        const req = httpMock.expectOne(`${environment.apiUrl}/rules/1`);
        expect(req.request.method).toBe('DELETE');
        req.flush({});
        tick();
    }));

    it('should handle 401 errors', fakeAsync(() => {
        service.get('/rules').subscribe(
            () => fail('should have failed'),
            error => expect(error.status).toBe(401)
        );

        httpMock.expectOne(`${environment.apiUrl}/rules`).error(
            new ErrorEvent('error', { message: 'Unauthorized' })
        );
        tick();
    }));

    it('should handle 404 errors', fakeAsync(() => {
        service.get('/rules/999').subscribe(
            () => fail('should have failed'),
            error => expect(error.status).toBe(404)
        );

        httpMock.expectOne(`${environment.apiUrl}/rules/999`).flush(null);
        tick();
    }));

    it('should include base URL in requests', fakeAsync(() => {
        service.get('/rules').subscribe();
        const req = httpMock.expectOne(`${environment.apiUrl}/rules`);
        expect(req.request.method).toBe('GET');
        req.flush([]);
        tick();
    }));

    it('should handle network errors', fakeAsync(() => {
        let errorReceived = false;
        service.get('/rules').subscribe(
            () => { },
            () => { errorReceived = true; }
        );

        httpMock.expectOne(`${environment.apiUrl}/rules`).error(
            new ProgressEvent('Network error')
        );
        tick();
        expect(errorReceived).toBe(true);
    }));
});

function fail(msg: string): never {
    throw new Error(msg);
}