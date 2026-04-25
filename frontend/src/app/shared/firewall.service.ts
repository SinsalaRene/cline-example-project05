import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { FirewallRule, ApiResponse, RuleFilter, ApprovalStatus, Statistics, PendingApproval, AuditLog } from './interfaces';

@Injectable({
    providedIn: 'root'
})
export class FirewallService {
    private api = inject(ApiService);

    getRules(filter?: RuleFilter, page: number = 1, perPage: number = 50): Observable<ApiResponse<FirewallRule>> {
        const params: Record<string, string> = {};
        if (filter) {
            if (filter.landing_zone) params['landing_zone'] = filter.landing_zone;
            if (filter.status?.length) params['status'] = filter.status.join(',');
            if (filter.action?.length) params['action'] = filter.action.join(',');
            if (filter.category?.length) params['category'] = filter.category.join(',');
            if (filter.workload) params['workload'] = filter.workload;
            if (filter.environment) params['environment'] = filter.environment;
            if (filter.search) params['search'] = filter.search;
            if (filter.priority_min !== undefined) params['priority_min'] = String(filter.priority_min);
            if (filter.priority_max !== undefined) params['priority_max'] = String(filter.priority_max);
        }
        params['page'] = String(page);
        params['per_page'] = String(perPage);
        if (filter?.sort_by) params['sort_by'] = filter.sort_by;
        if (filter?.sort_order) params['sort_order'] = filter.sort_order;

        return this.api.get<ApiResponse<FirewallRule>>('/rules', params);
    }

    getRule(id: number): Observable<FirewallRule> {
        return this.api.get<FirewallRule>(`/rules/${id}`);
    }

    createRule(rule: FirewallRule): Observable<FirewallRule> {
        return this.api.post<FirewallRule>('/rules', rule);
    }

    updateRule(id: number, rule: FirewallRule): Observable<FirewallRule> {
        return this.api.put<FirewallRule>(`/rules/${id}`, rule);
    }

    archiveRule(id: number): Observable<{ message: string }> {
        return this.api.delete<{ message: string }>(`/rules/${id}`);
    }

    getRuleAuditLogs(id: number, page: number = 1, perPage: number = 50): Observable<any> {
        return this.api.get(`/rules/${id}/audit`, { page: String(page), per_page: String(perPage) });
    }

    getStatistics(): Observable<Statistics> {
        return this.api.get<Statistics>('/statistics');
    }
}