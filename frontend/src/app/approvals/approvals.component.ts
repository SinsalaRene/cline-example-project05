import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../app/shared/auth.service';
import { ApprovalService } from '../../app/shared/approval.service';
import { FirewallService } from '../../app/shared/firewall.service';
import { PendingApproval, FirewallRule } from '../../app/shared/interfaces';

@Component({
    selector: 'app-approvals',
    template: `
        <div class="page-header">
            <h1>Pending Approvals</h1>
            <span class="badge badge-pending">{{pendingCount}} pending</span>
        </div>

        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">{{pendingCount}}</div>
                <div class="stat-label">Pending My Approval</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{approvedToday}}</div>
                <div class="stat-label">Approved Today</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{totalReviewd}}</div>
                <div class="stat-label">Total Reviewed</div>
            </div>
        </div>

        <div class="card" style="margin:16px 32px;">
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Rule</th>
                        <th>Collection</th>
                        <th>Action</th>
                        <th>Priority</th>
                        <th>Requested By</th>
                        <th>Requires</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr *ngFor="let item of pendingItems">
                        <td>
                            <a (click)="viewRule(item.rule_id!)" style="cursor:pointer; color:#007bff;">
                                {{item.rule_name}}
                            </a>
                        </td>
                        <td>-</td>
                        <td><span class="badge badge-action-allow">Allow</span></td>
                        <td>100</td>
                        <td>john.doe</td>
                        <td>{{item.approver_role}}</td>
                        <td><span class="badge badge-pending">{{item.status}}</span></td>
                        <td>
                            <button (click)="approve(item)" class="btn btn-success btn-sm">Approve</button>
                            <button (click)="reject(item)" class="btn btn-danger btn-sm">Reject</button>
                            <button (click)="viewRule(item.rule_id!)" class="btn btn-sm btn-outline">View</button>
                        </td>
                    </tr>
                    <tr *ngIf="!pendingItems.length">
                        <td colspan="8" style="text-align:center; padding:32px;">
                            No pending approvals.
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Approve/Reject Modal -->
        <div *ngIf="showModal" class="modal-overlay" (click)="closeModal()">
            <div class="modal-content" (click)="$event.stopPropagation()">
                <h3>{{modalAction === 'approve' ? 'Approve' : 'Reject'}} Rule</h3>
                <div class="form-group">
                    <label>Notes (optional)</label>
                    <textarea [(ngModel)]="modalNotes" placeholder="Add a note..."></textarea>
                </div>
                <div style="display:flex; gap:12px;">
                    <button (click)="executeModal()" class="btn btn-primary">Confirm</button>
                    <button (click)="closeModal()" class="btn btn-outline">Cancel</button>
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
        .badge-pending { background: #cce5ff; color: #004085; }
        .badge-action-allow { background: #d4edda; color: #155724; }
        .stats-row { display: flex; gap: 16px; padding: 20px 32px; }
        .stat-card {
            flex: 1;
            background: #fff;
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
        }
        .stat-card .stat-value { font-size: 28px; font-weight: 700; color: #333; }
        .stat-card .stat-label { font-size: 13px; color: #888; margin-top: 4px; }
        .card {
            background: #fff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: #fff;
        }
        .data-table th {
            background: #f5f7fa;
            padding: 12px 16px;
            text-align: left;
            font-weight: 600;
            font-size: 13px;
            color: #666;
            border-bottom: 2px solid #e0e0e0;
        }
        .data-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 14px;
        }
        .data-table tr:hover { background: #f9fbff; }
        .btn {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
            font-size: 12px;
            font-weight: 500;
        }
        .btn-sm { padding: 4px 12px; font-size: 12px; }
        .btn-primary { background: #007bff; color: #fff; }
        .btn-success { background: #28a745; color: #fff; }
        .btn-danger { background: #dc3545; color: #fff; }
        .btn-outline { background: transparent; border: 1px solid #007bff; color: #007bff; }
        .modal-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal-content {
            background: #fff;
            border-radius: 12px;
            padding: 32px;
            width: 500px;
            max-width: 90vw;
        }
        .modal-content h3 { margin-bottom: 16px; }
        .form-group { margin-bottom: 16px; }
        .form-group label { display: block; margin-bottom: 4px; font-weight: 500; }
        .form-group textarea {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            min-height: 80px;
            resize: vertical;
        }
    `])
export class ApprovalsComponent implements OnInit {
    private approvalService = inject(ApprovalService);
    private authService = inject(AuthService);
    private router = inject(Router);

    pendingItems: PendingApproval[] = [];
    pendingCount = 0;
    approvedToday = 0;
    totalReviewed = 0;

    showModal = false;
    modalAction: 'approve' | 'reject' = 'approve';
    modalNotes = '';
    currentApproval: PendingApproval | null = null;

    ngOnInit(): void {
        this.loadPending();
    }

    loadPending(): void {
        this.approvalService.getPendingApprovals().subscribe({
            next: (data) => {
                this.pendingItems = data.items || [];
                this.pendingCount = data.total || 0;
            }
        });
    }

    viewRule(id: number): void {
        this.router.navigate(['/rules', id]);
    }

    approve(item: PendingApproval): void {
        this.currentApproval = item;
        this.modalAction = 'approve';
        this.modalNotes = '';
        this.showModal = true;
    }

    reject(item: PendingApproval): void {
        this.currentApproval = item;
        this.modalAction = 'reject';
        this.modalNotes = '';
        this.showModal = true;
    }

    executeModal(): void {
        if (!this.currentApproval) return;
        const approved = this.modalAction === 'approve';
        this.approvalService.submitApproval(
            this.currentApproval.approval_record_id!,
            { approved, notes: this.modalNotes }
        ).subscribe({
            next: () => {
                this.closeModal();
                this.loadPending();
            }
        });
    }

    closeModal(): void {
        this.showModal = false;
        this.currentApproval = null;
        this.modalNotes = '';
    }
}