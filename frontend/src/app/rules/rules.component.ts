import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { ApiService } from '../../app/shared/api.service';
import { FirewallService } from '../../app/shared/firewall.service';
import { AuthService } from '../../app/shared/auth.service';
import { FirewallRule, ApiResponse, RuleFilter } from '../../app/shared/interfaces';

@Component({
    selector: 'app-rules',
    template: `
        <div class="page-header">
            <h1>Firewall Rules</h1>
            <button (click)="openCreate()" class="btn btn-primary">+ New Rule</button>
        </div>

        <div class="filters-bar">
            <input [(ngModel)]="filters.search" (input)="onSearch()" [placeholder]="'Search rules...'"/>
            <select [(ngModel)]="filters.landing_zone" (change)="onFilter()">
                <option value="">All Zones</option>
                <option value="prod">Production</option>
                <option value="dev">Development</option>
                <option value="test">Test</option>
            </select>
            <select [(ngModel)]="filters.status" (change)="onFilter()">
                <option value="">All Statuses</option>
                <option value="active">Active</option>
                <option value="draft">Draft</option>
                <option value="pending_approval">Pending Approval</option>
                <option value="archived">Archived</option>
            </select>
            <select [(ngModel)]="filters.action" (change)="onFilter()">
                <option value="">All Actions</option>
                <option value="allow">Allow</option>
                <option value="deny">Deny</option>
            </select>
        </div>

        <table class="data-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Collection</th>
                    <th>Action</th>
                    <th>Priority</th>
                    <th>Source</th>
                    <th>Destination</th>
                    <th>Status</th>
                    <th>Category</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                <tr *ngFor="let rule of rules">
                    <td>
                        <a (click)="viewRule(rule.id!)" style="cursor:pointer; color:#007bff;">{{rule.name}}</a>
                    </td>
                    <td>{{rule.rule_collection_name}}</td>
                    <td>
                        <span [class]="'badge badge-action-' + rule.action">
                            {{rule.action || 'N/A'}}
                        </span>
                    </td>
                    <td>{{rule.priority || '-'}}</td>
                    <td>{{rule.source_addresses?.join(', ') || '-'}}</td>
                    <td>{{rule.destination_addresses?.join(', ') || '-'}}</td>
                    <td>
                        <span [class]="'badge badge-' + rule.status">
                            {{rule.status || 'draft'}}
                        </span>
                    </td>
                    <td>{{rule.category || '-'}}</td>
                    <td>
                        <button (click)="viewRule(rule.id!)" class="btn btn-sm btn-outline">View</button>
                    </td>
                </tr>
                <tr *ngIf="!rules.length">
                    <td colspan="9" style="text-align:center; padding:32px;">
                        No rules found. Click "+ New Rule" to create one.
                    </td>
                </tr>
            </tbody>
        </table>

        <div class="pagination" *ngIf="totalPages > 1">
            <button (click)="prevPage()" [disabled]="currentPage === 1">Previous</button>
            <span>Page {{currentPage}} of {{totalPages}}</span>
            <button (click)="nextPage()" [disabled]="currentPage >= totalPages">Next</button>
        </div>

        <div class="card" *ngIf="showCreateForm">
            <h3>New Firewall Rule</h3>
            <form [formGroup]="ruleForm" (ngSubmit)="onSubmit()">
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                    <div class="form-group">
                        <label>Rule Name *</label>
                        <input formControlName="name" placeholder="Allow-Web-Traffic"/>
                    </div>
                    <div class="form-group">
                        <label>Collection Name *</label>
                        <input formControlName="rule_collection_name" placeholder="Web-Collections"/>
                    </div>
                    <div class="form-group">
                        <label>Landing Zone *</label>
                        <select formControlName="landing_zone">
                            <option value="prod">Production</option>
                            <option value="dev">Development</option>
                            <option value="test">Test</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Priority</label>
                        <input formControlName="priority" type="number" placeholder="100"/>
                    </div>
                    <div class="form-group">
                        <label>Action</label>
                        <select formControlName="action">
                            <option value="allow">Allow</option>
                            <option value="deny">Deny</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <input formControlName="category" placeholder="network, application"/>
                    </div>
                </div>
                <div class="form-group">
                    <label>Description</label>
                    <textarea formControlName="description" placeholder="Describe this rule..."></textarea>
                </div>
                <div class="form-group">
                    <label>Source Addresses (comma-separated)</label>
                    <input formControlName="source_addresses" placeholder="10.0.0.0/8, 192.168.1.0/24"/>
                </div>
                <div class="form-group">
                    <label>Destination Addresses (comma-separated)</label>
                    <input formControlName="destination_addresses" placeholder="20.0.0.0/8"/>
                </div>
                <div class="form-group">
                    <label>Destination Ports (comma-separated)</label>
                    <input formControlName="destination_ports" placeholder="443, 80"/>
                </div>
                <div class="form-group">
                    <label>Destination FQDNs (comma-separated)</label>
                    <input formControlName="destination_fqdns" placeholder="*.example.com"/>
                </div>
                <div style="display:flex; gap:12px;">
                    <button type="submit" class="btn btn-primary">Create & Submit for Review</button>
                    <button type="button" (click)="showCreateForm=false" class="btn btn-outline">Cancel</button>
                </div>
            </form>
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
        .filters-bar {
            display: flex;
            gap: 12px;
            padding: 16px 32px;
            background: #fff;
            border-bottom: 1px solid #e0e0e0;
            align-items: center;
            flex-wrap: wrap;
        }
        .filters-bar input, .filters-bar select {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .filters-bar input { flex: 1; min-width: 200px; }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: #fff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
            margin: 16px 0;
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
        .btn-sm { padding: 4px 12px; font-size: 12px; }
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            padding: 16px;
        }
        .pagination button {
            padding: 6px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background: #fff;
            cursor: pointer;
        }
        .pagination button:disabled { opacity: 0.5; cursor: default; }
        .pagination span { font-size: 14px; color: #888; }
        .card {
            background: #fff;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
        }
        .card h3 { margin-bottom: 16px; }
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            margin-bottom: 4px;
            font-weight: 500;
            font-size: 14px;
            color: #555;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .form-group textarea { min-height: 80px; resize: vertical; }
    `])
export class RulesComponent implements OnInit {
    private firewallService = inject(FirewallService);
    private authService = inject(AuthService);
    private router = inject(Router);
    private fb = inject(FormBuilder);

    rules: FirewallRule[] = [];
    loading = false;
    currentPage = 1;
    totalPages = 1;
    total = 0;

    filters: RuleFilter = {
        landing_zone: '',
        status: undefined,
        action: undefined,
        category: undefined,
        workload: '',
        environment: '',
        search: '',
        priority_min: undefined,
        priority_max: undefined,
        sort_by: 'name',
        sort_order: 'asc'
    };

    showCreateForm = false;
    ruleForm!: FormGroup;

    ngOnInit(): void {
        this.ruleForm = this.fb.group({
            name: ['', Validators.required],
            description: [''],
            rule_collection_name: ['', Validators.required],
            landing_zone: ['prod'],
            priority: [100],
            action: ['allow'],
            category: [''],
            source_addresses: [''],
            destination_addresses: [''],
            destination_ports: [''],
            destination_fqdns: [''],
            subscription_id: [''],
            resource_group: [''],
            firewall_policy: [''],
            workload: [''],
            workload_type: [''],
            environment: [''],
            tags: [[]]
        });
        this.loadRules();
    }

    loadRules(): void {
        this.loading = true;
        this.firewallService.getRules(this.filters, this.currentPage).subscribe({
            next: (data) => {
                this.rules = data.items || [];
                this.total = data.total || 0;
                this.totalPages = Math.ceil((data.total || 0) / 50);
                this.loading = false;
            },
            error: (err) => {
                console.error('Failed to load rules:', err);
                this.loading = false;
            }
        });
    }

    onSearch(): void {
        this.currentPage = 1;
        this.loadRules();
    }

    onFilter(): void {
        this.currentPage = 1;
        this.loadRules();
    }

    viewRule(id: number): void {
        this.router.navigate(['/rules', id]);
    }

    openCreate(): void {
        this.showCreateForm = true;
    }

    onSubmit(): void {
        if (this.ruleForm.invalid) {
            this.ruleForm.markAllAsTouched();
            return;
        }
        const formValues = this.ruleForm.value;
        const rule: FirewallRule = {
            ...formValues,
            name: formValues.name,
            rule_collection_name: formValues.rule_collection_name,
            landing_zone: formValues.landing_zone,
            action: formValues.action,
            priority: formValues.priority || 100,
            description: formValues.description || '',
            category: formValues.category || '',
            source_addresses: formValues.source_addresses ? formValues.source_addresses.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
            destination_addresses: formValues.destination_addresses ? formValues.destination_addresses.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
            destination_ports: formValues.destination_ports ? formValues.destination_ports.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
            destination_fqdns: formValues.destination_fqdns ? formValues.destination_fqdns.split(',').map((s: string) => s.trim()).filter(Boolean) : []
        };
        this.firewallService.createRule(rule).subscribe({
            next: (created) => {
                this.showCreateForm = false;
                this.ruleForm.reset();
                this.loadRules();
            },
            error: (err) => {
                console.error('Failed to create rule:', err);
            }
        });
    }

    prevPage(): void {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadRules();
        }
    }

    nextPage(): void {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadRules();
        }
    }
}