import { TestBed, fakeAsync, tick } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpClient } from '@angular/common/http';

import { ApprovalService } from './approval.service';
import { environment } from '../../environments/environment';

describe('ApprovalService', () => {
    let service: ApprovalService;
    let httpMock: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                ApprovalService,
                provideHttpClientTesting()
            ]
        });
        service = TestBed.inject(ApprovalService);
        httpMock = TestBed.inject(HttpTestingController);
    });

    afterEach(() => {
        httpMock.verify();
    });

    it('should be created', () => {
        expect(service).toBeTruthy();
    });

    it('should get pending approvals', fakeAsync(() => {
        service.getPendingApprovals().subscribe(approvals => {
            expect(approvals).toEqual([
                { id: 1, rule_id: 1, action: 'approve', notes: 'Approved' },
                { id: 2, rule_id: 2, action: 'reject', notes: 'Rejected' }
            ]);
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/approvals/pending`);
        expect(req.request.method).toBe('GET');
        req.flush([
            { id: 1, rule_id: 1, action: 'approve', notes: 'Approved' },
            { id: 2, rule_id: 2, action: 'reject', notes: 'Rejected' }
        ]);
        tick();
    }));

    it('should submit approval decision', fakeAsync(() => {
        service.approveRule(1, { action: 'approve', notes: 'Approved for production' }).subscribe(response => {
            expect(response).toEqual({ id: 1, status: 'approved' });
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/approvals/1`);
        expect(req.request.method).toBe('POST');
        expect(req.request.body).toEqual({ action: 'approve', notes: 'Approved for production' });
        req.flush({ id: 1, status: 'approved' });
        tick();
    }));

    it('should handle 404 on invalid approval', fakeAsync(() => {
        service.approveRule(999, { action: 'approve', notes: 'Test' }).subscribe(
            () => fail('should have failed'),
            error => expect(error.status).toBe(404)
        );

        httpMock.expectOne(`${environment.apiUrl}/approvals/999`).error(
            new ErrorEvent('error', { message: 'Not Found' })
        );
        tick();
    }));

    it('should get approval history for a rule', fakeAsync(() => {
        service.getApprovalHistory(1).subscribe(history => {
            expect(history).toEqual([
                { id: 1, rule_id: 1, user_id: 1, action: 'approve', notes: 'First approval' },
                { id: 2, rule_id: 1, user_id: 2, action: 'reject', notes: 'Rejected' }
            ]);
        });

        const req = httpMock.expectOne(`${environment.apiUrl}/approvals/rule/1`);
        expect(req.request.method).toBe('GET');
        req.flush([
            { id: 1, rule_id: 1, user_id: 1, action: 'approve', notes: 'First approval' },
            { id: 2, rule_id: 1, user_id: 2, action: 'reject', notes: 'Rejected' }
        ]);
        tick();
    }));

    it('should handle network errors gracefully', fakeAsync(() => {
        let errorReceived: any = null;

        service.getPendingApprovals().subscribe(
            () => { },
            (error) => { errorReceived = error; }
        );

        httpMock.expectOne(`${environment.apiUrl}/approvals/pending`).error(
            new ProgressEvent('Network error')
        );
        tick();

        expect(errorReceived).toBeDefined();
    }));

    it('should set auth headers on approval requests', fakeAsync(() => {
        localStorage.setItem('access_token', 'test-token');
        service.approveRule(1, { action: 'approve', notes: 'Test' }).subscribe();

        const req = httpMock.expectOne(`${environment.apiUrl}/approvals/1`);
        expect(req.request.headers.get('Authorization')).toBe('Bearer test-token');
        req.flush({ id: 1 });
        tick();
    }));
});