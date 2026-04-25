import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { PendingApproval, ApprovalStatus } from './interfaces';

@Injectable({
    providedIn: 'root'
})
export class ApprovalService {
    private api = inject(ApiService);

    getPendingApprovals(page: number = 1, perPage: number = 50): Observable<any> {
        return this.api.get(`/approvals/pending`, { page: String(page), per_page: String(perPage) });
    }

    getPendingByRole(): Observable<any> {
        return this.api.get('/approvals/pending/by-role');
    }

    submitApproval(recordId: number, data: { approved: boolean; notes?: string }): Observable<any> {
        return this.api.patch(`/approvals/${recordId}/approve`, data);
    }

    getRuleApprovals(ruleId: number): Observable<ApprovalStatus> {
        return this.api.get<ApprovalStatus>(`/rules/${ruleId}/approvals`);
    }

    submitForApproval(ruleId: number, data?: { approvers?: string[] }): Observable<any> {
        return this.api.post(`/rules/${ruleId}/submit`, data || {});
    }

    getApprovalAuditTrail(ruleId: number): Observable<any> {
        return this.api.get(`/rules/${ruleId}/audit`);
    }
}