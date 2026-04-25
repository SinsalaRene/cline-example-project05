import { Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { FirewallService } from '../../shared/firewall.service';
import { ApprovalService } from '../../shared/approval.service';
import { AuthService } from '../../shared/auth.service';
import { FirewallRule, ApprovalStatus, AuditLog } from '../../shared/interfaces';

@Component({
    selector: 'app-rule-detail',
    template: `
        <div class="page-header">
            <div>
                <button (click)="goBack()" class="btn btn-outline" style="margin-bottom:8px;">&larr; Back</button>
                <h1>{{rule?.name || 'Rule Details'}}</h1>
            </div>
            <div *ngIf="rule">
                <span [class]="'badge badge-' + rule.status">{{rule.status || 'draft'}}</span>
            </div>
        </div>

        <div *ngIf="loading" style="padding:32px; text-align:center;">Loading...</div>

        <div *ngIf="!loading && rule">
            <div style="display:grid; grid-template-columns:2fr 1fr; gap:16px; padding:20px 32px;">
                <!-- Main info -->
                <div class="card">
                    <div class="detail-section">
                        <h3>Basic Information</h3>
                        <div class="detail-row"><span class="label">Name:</span><span class="value">{{rule.name}}</span></div>
                        <div class="detail-row"><span class="label">Description:</span><span class="value">{{rule.description || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Collection:</span><span class="value">{{rule.rule_collection_name}}</span></div>
                        <div class="detail-row"><span class="label">Priority:</span><span class="value">{{rule.priority || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Action:</span><span class="value"><span class="badge badge-action-{{rule.action}}">{{rule.action}}</span></span></div>
                        <div class="detail-row"><span class="label">Category:</span><span class="value">{{rule.category || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Status:</span><span class="value"><span class="badge badge-{{rule.status}}">{{rule.status}}</span></span></div>
                    </div>

                    <div class="detail-section">
                        <h3>Network Configuration</h3>
                        <div class="detail-row"><span class="label">Source:</span><span class="value">{{rule.source_addresses?.join(', ') || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Destination:</span><span class="value">{{rule.destination_addresses?.join(', ') || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Ports:</span><span class="value">{{rule.destination_ports?.join(', ') || '-'}}</span></div>
                        <div class="detail-row"><span class="label">FQDNs:</span><span class="value">{{rule.destination_fqdns?.join(', ') || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Protocols:</span><span class="value">{{rule.protocols?.join(', ') || '-'}}</span></div>
                    </div>

                    <div class="detail-section">
                        <h3>Azure Information</h3>
                        <div class="detail-row"><span class="label">Landing Zone:</span><span class="value">{{rule.landing_zone}}</span></div>
                        <div class="detail-row"><span class="label">Subscription:</span><span class="value">{{rule.subscription_id || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Resource Group:</span><span class="value">{{rule.resource_group || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Firewall Policy:</span><span class="value">{{rule.firewall_policy || '-'}}</span></div>
                    </div>
                </div>

                <!-- Sidebar -->
                <div>
                    <div class="card">
                        <h3>Actions</h3>
                        <div style="display:flex; flex-direction:column; gap:8px;">
                            <button *ngIf="rule.status === 'draft'" (click)="submitForApproval()" class="btn btn-primary">Submit for Approval</button>
                            <button *ngIf="rule.status === 'pending_approval'" class="btn btn-primary" disabled>Pending Approval</button>
                            <button *ngIf="rule.status === 'active'" (click)="editRule()" class="btn btn-outline">Edit Rule</button>
                            <button *ngIf="rule.status !== 'archived'" (click)="archiveRule()" class="btn btn-danger">Archive</button>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Approval Status</h3>
                        <div *ngIf="approvalData">
                            <div class="approval-flow">
                                <div *ngFor="let a of approvalData.approvals" [class]="'approval-step ' + a.status">
                                    {{a.approver_role}}: {{a.status}}
                                </div>
                            </div>
                        </div>
                        <div *ngIf="!approvalData && rule.status === 'draft'">
                            <p style="color:#888; font-size:14px;">No approvals yet.</p>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Audit Log</h3>
                        <div *ngFor="let log of auditLogs" class="audit-entry">
                            <div class="audit-time">{{log.timestamp}}</div>
                            <div>
                                <span class="audit-user">{{log.username || 'System'}}</span>
                                <span class="audit-action"> {{log.action}}</span>
                            </div>
                        </div>
                    </div>

                    <div class="card">
                        <h3>Metadata</h3>
                        <div class="detail-row"><span class="label">Created:</span><span class="value">{{rule.created_at || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Updated:</span><span class="value">{{rule.updated_at || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Created by:</span><span class="value">{{rule.created_by || '-'}}</span></div>
                        <div class="detail-row"><span class="label">Approved:</span><span class="value">{{rule.approved_by ? rule.approved_at : '-'}}</span></div>
                    </div>
                </div>
            </div>
        </div>
    `,
    styles: [`
        .page-header {
            padding: 24px 32px;
            background: #fff;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .page-header h1 { font-size: 24px; font-weight: 600; color: #333; }
        .badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .badge-active { background: #d4edda; color: #155724; }
        .badge-draft { background: #fff3cd; color: #856404; }
        .badge-pending { background: #cce5ff; color: #004085; }
        .badge-archived { background: #e2e3e5; color: #383d41; }
        .badge-action-allow { background: #d4edda; color: #155724; }
        .badge-action-deny { background: #f8d7da; color: #721c24; }
        .btn {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
        }
        .btn-primary { background: #007bff; color: #fff; }
        .btn-outline { background: transparent; border: 1px solid #007bff; color: #007bff; }
        .btn-danger { background: #dc3545; color: #fff; }
        .btn:disabled { opacity: 0.5; cursor: default; }
        .card {
            background: #fff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
        }
        .card h3 {
            font-size: 16px;
            font-weight: 600;
            color: #555;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e0e0e0;
        }
        .detail-section { margin-bottom: 24px; }
        .detail-section h3 {
            font-size: 16px;
            font-weight: 600;
            color: #555;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e0e0e0;
        }
        .detail-row {
            display: flex;
            padding: 6px 0;
            font-size: 14px;
        }
        .detail-row .label { width: 140px; font-weight: 500; color: #888; }
        .detail-row .value { flex: 1; color: #333; }
        .approval-flow { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .approval-step {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 13px;
            background: #f5f7fa;
        }
        .approval-step.approved { background: #d4edda; }
        .approval-step.pending { background: #cce5ff; }
        .audit-entry { padding: 10px 0; border-bottom: 1px solid #f0f0f0; font-size: 13px; }
        .audit-entry .audit-time { color: #888; }
        .audit-entry .audit-user { font-weight: 500; color: #007bff; }
        .audit-entry .audit-action { color: #333; }
    `])
export class RuleDetailComponent implements OnInit {
    private route = inject(ActivatedRoute);
    private router = inject(Router);
    private firewallService = inject(FirewallService);
    private approvalService = inject(ApprovalService);
    private authService = inject(AuthService);

    ruleId!: number;
    rule: FirewallRule | null = null;
    approvalData: ApprovalStatus | null = null;
    auditLogs: AuditLog[] = [];
    loading = false;

    ngOnInit(): void {
        this.ruleId = Number(this.route.snapshot.paramMap.get('id'));
        this.loadRule();
    }

    loadRule(): void {
        this.loading = true;
        this.firewallService.getRule(this.ruleId).subscribe({
            next: (rule) => {
                this.rule = rule;
                this.loadApprovals();
                this.loadAuditLogs();
                this.loading = false;
            },
            error: () => { this.loading = false; }
        });
    }

    loadApprovals(): void {
        this.approvalService.getRuleApprovals(this.ruleId).subscribe({
            next: (data) => { this.approvalData = data; }
        });
    }

    loadAuditLogs(): void {
        this.firewallService.getRuleAuditLogs(this.ruleId).subscribe({
            next: (data) => { this.auditLogs = data.items || []; }
        });
    }

    goBack(): void {
        this.router.navigate(['/rules']);
    }

    submitForApproval(): void {
        if (confirm('Submit this rule for approval?')) {
            this.approvalService.submitForApproval(this.ruleId).subscribe({
                next: () => { this.loadRule(); }
            });
        }
    }

    editRule(): void {
        alert('Edit functionality - would open edit modal');
    }

    archiveRule(): void {
        if (confirm('Archive this rule? This action cannot be undone.')) {
            this.firewallService.archiveRule(this.ruleId).subscribe({
                next: () => { this.router.navigate(['/rules']); }
            });
        }
    }
}