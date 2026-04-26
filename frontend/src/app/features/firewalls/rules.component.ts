import { Component, OnInit, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FirewallRule, RuleFilter, User } from '../../shared/interfaces';
import { FirewallService } from '../../shared/firewall.service';
import { AuthService } from '../../core/services/auth.service';
import { ConfirmDialogComponent } from '../../shared/components/confirm-dialog.component';

@Component({
    selector: 'app-rules',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatButtonModule,
        MatInputModule,
        MatFormFieldModule,
        MatSelectModule,
        MatTableModule,
        MatPaginatorModule,
        MatSortModule,
        MatChipsModule,
        MatIconModule,
        RouterLink
    ],
    changeDetection: ChangeDetectionStrategy.OnPush,
    template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h1>Firewall Rules</h1>
          <p class="subtitle">Manage Azure firewall rules and policies</p>
        </div>
        <div class="actions">
          <button mat-raised-button color="primary" routerLink="/rules/create">
            Create Rule
          </button>
        </div>
      </div>

      <div class="filters">
        <mat-form-field>
          <mat-label>Search</mat-label>
          <input matInput placeholder="Search rules..." [(ngModel)]="filters.search">
        </mat-form-field>
        <mat-form-field>
          <mat-label>Landing Zone</mat-label>
          <mat-select [(ngModel)]="filters.landing_zone">
            <option value="">All</option>
            <option value="corp">Corp</option>
            <option value="landing">Landing Zone</option>
          </mat-select>
        </mat-form-field>
        <button mat-stroked-button (click)="applyFilters()">Filter</button>
      </div>

      <div class="table-container">
        <table matSort [dataSource]="dataSource" matTable>
          <ng-container matColumnDef="name">
            <th mat-header-cell *matHeaderCellDef>Rule Name</th>
            <td mat-cell *matCellDef="let rule">
              <a routerLink="/rules/{{rule.id}}" class="link">{{rule.name}}</a>
            </td>
          </ng-container>

          <ng-container matColumnDef="status">
            <th mat-header-cell *matHeaderCellDef>Status</th>
            <td mat-cell *matCellDef="let rule">
              <mat-chip [ngClass]="getStatusColor(rule.status)">
                {{rule.status}}
              </mat-chip>
            </td>
          </ng-container>

          <ng-container matColumnDef="action">
            <th mat-header-cell *matHeaderCellDef>Action</th>
            <td mat-cell *matCellDef="let rule">{{rule.action}}</td>
          </ng-container>

          <ng-container matColumnDef="priority">
            <th mat-header-cell *matHeaderCellDef>Priority</th>
            <td mat-cell *matCellDef="let rule">{{rule.priority}}</td>
          </ng-container>

          <ng-container matColumnDef="actions">
            <th mat-header-cell *matHeaderCellDef>Actions</th>
            <td mat-cell *matCellDef="let rule">
              <button mat-icon-button routerLink="/rules/{{rule.id}}">
                <mat-icon>visibility</mat-icon>
              </button>
              <button mat-icon-button (click)="deleteRule(rule)">
                <mat-icon>delete</mat-icon>
              </button>
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
        </table>
        <mat-paginator [pageSizeOptions]="[10, 25, 50]" [pageSize]="10"></mat-paginator>
      </div>
    </div>
  `,
    styles: [`
    .page {
      padding: 24px;
      max-width: 1200px;
      margin: 0 auto;
    }

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      flex-wrap: wrap;
      gap: 16px;
    }

    .page-header h1 {
      font-size: 24px;
      font-weight: 600;
      margin: 0;
      color: #24244d;
    }

    .page-header .subtitle {
      margin: 4px 0 0;
      color: #666;
      font-size: 14px;
    }

    .filters {
      display: flex;
      gap: 16px;
      margin-bottom: 24px;
      flex-wrap: wrap;
      align-items: center;
    }

    .filters mat-form-field {
      min-width: 200px;
    }

    .table-container {
      overflow-x: auto;
      border: 1px solid #e0e0e0;
      border-radius: 4px;
    }

    .link {
      color: #1976d2;
      text-decoration: underline;
      cursor: pointer;
    }

    .link:hover {
      color: #1565c0;
    }

    .status-draft { background-color: #fff3cd; color: #856404; }
    .status-pending { background-color: #cce5ff; color: #004085; }
    .status-active { background-color: #d4edda; color: #155724; }
    .status-inactive { background-color: #e2e3e5; color: #383d41; }

    @media (max-width: 768px) {
      .page { padding: 16px; }
      .page-header { flex-direction: column; align-items: stretch; }
      .filters { flex-direction: column; }
      .filters mat-form-field { min-width: 100%; }
    }
  `]
})
export class RulesComponent implements OnInit {
    private firewallService = inject(FirewallService);
    private authService = inject(AuthService);
    private router = inject(Router);
    private route = inject(ActivatedRoute);
    private dialog = inject(MatDialog);

    rules: FirewallRule[] = [];
    displayedColumns: string[] = ['name', 'status', 'action', 'priority', 'actions'];
    dataSource: any;
    filters: RuleFilter = {};

    ngOnInit(): void {
        this.loadRules();
    }

    loadRules(): void {
        this.firewallService.getRules(this.filters as RuleFilter).subscribe({
            next: (data) => {
                this.rules = data.items || [];
                this.dataSource = data;
            }
        });
    }

    applyFilters(): void {
        this.router.navigate([], { relativeTo: this.route, queryParams: this.filters });
    }

    deleteRule(rule: FirewallRule): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            data: {
                title: 'Delete Rule',
                message: `Are you sure you want to delete "${rule.name}"?`,
                confirmText: 'Delete',
                cancelText: 'Cancel'
            }
        });

        dialogRef.afterClosed().subscribe(confirmed => {
            if (confirmed && rule.id) {
                this.firewallService.deleteRule(rule.id).subscribe(() => {
                    this.loadRules();
                });
            }
        });
    }

    getStatusColor(status: string): string {
        const colors: Record<string, string> = {
            'DRAFT': 'status-draft',
            'PENDING': 'status-pending',
            'ACTIVE': 'status-active',
            'INACTIVE': 'status-inactive'
        };
        return colors[status] || '';
    }
}