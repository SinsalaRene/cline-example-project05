import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { Statistics } from '../../shared/interfaces';
import { FirewallService } from '../../shared/firewall.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MatButtonModule, MatCardModule],
  template: `
    <div class="dashboard">
      <h1>Dashboard</h1>

      <div class="stats-grid">
        <mat-card>
          <mat-card-content>
            <h3>Total Rules</h3>
            <div class="stat-value">{{stats?.total || 0}}</div>
          </mat-card-content>
        </mat-card>

        <mat-card>
          <mat-card-content>
            <h3>Active Rules</h3>
            <div class="stat-value">{{stats?.by_status?.ACTIVE || 0}}</div>
          </mat-card-content>
        </mat-card>

        <mat-card>
          <mat-card-content>
            <h3>Pending Approvals</h3>
            <div class="stat-value">{{stats?.by_status?.PENDING || 0}}</div>
          </mat-card-content>
        </mat-card>

        <mat-card>
          <mat-card-content>
            <h3>Allow Rules</h3>
            <div class="stat-value">{{stats?.by_action?.ALLOW || 0}}</div>
          </mat-card-content>
        </mat-card>
      </div>

      <div class="charts-row">
        <mat-card>
          <mat-card-header><mat-card-title>By Status</mat-card-title></mat-card-header>
          <div class="chart-container">
            <div class="status-chart" *ngIf="stats?.by_status">
              <div *ngFor="let item of statusEntries()" class="chart-item">
                <span class="label">{{item.key}}</span>
                <span class="value">{{item.value}}</span>
                <div class="bar" [style.width.%]="getPercentage(item.value, totalStatus)">
                </div>
              </div>
            </div>
          </div>
        </mat-card>

        <mat-card>
          <mat-card-header><mat-card-title>By Landing Zone</mat-card-title></mat-card-header>
          <div class="chart-container">
            <div class="zone-chart" *ngIf="stats?.by_landing_zone">
              <div *ngFor="let item of zoneEntries()" class="chart-item">
                <span class="label">{{item.key}}</span>
                <span class="value">{{item.value}}</span>
                <div class="bar" [style.width.%]="getPercentage(item.value, totalZone)">
                </div>
              </div>
            </div>
          </div>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .dashboard { padding: 24px; max-width: 1200px; margin: 0 auto; }

    .dashboard h1 {
      font-size: 24px;
      font-weight: 600;
      margin-bottom: 24px;
      color: #24244d;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 16px;
      margin: 20px 0;
    }

    .stat-value {
      font-size: 32px;
      font-weight: 600;
      color: #1976d2;
      margin-top: 8px;
    }

    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 20px;
    }

    .chart-container {
      padding: 16px;
      min-height: 200px;
    }

    mat-card-header { margin-bottom: 16px; }

    .chart-item {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
      position: relative;
    }

    .chart-item .label {
      width: 80px;
      font-size: 13px;
      font-weight: 500;
      color: #333;
      flex-shrink: 0;
    }

    .chart-item .value {
      width: 40px;
      font-size: 13px;
      text-align: right;
      margin-left: 8px;
      flex-shrink: 0;
    }

    .chart-item .bar {
      height: 20px;
      background: linear-gradient(90deg, #1976d2, #42a5f5);
      border-radius: 4px;
      min-width: 2px;
      transition: width 0.3s ease;
    }

    @media (max-width: 768px) {
      .dashboard { padding: 16px; }
      .stats-grid { grid-template-columns: repeat(2, 1fr); }
      .charts-row { grid-template-columns: 1fr; }
      .stat-value { font-size: 24px; }
    }
  `],
  providers: []
})
export class DashboardComponent implements OnInit {
  private firewallService = inject(FirewallService);

  stats: Statistics | null = null;
  totalStatus = 0;
  totalZone = 0;

  statusEntries = () => {
    if (!this.stats?.by_status) return [];
    return Object.entries(this.stats.by_status).map(([key, value]) => ({ key, value: value as number }));
  };

  zoneEntries = () => {
    if (!this.stats?.by_landing_zone) return [];
    return Object.entries(this.stats.by_landing_zone).map(([key, value]) => ({ key, value: value as number }));
  };

  getPercentage(value: number, total: number): number {
    if (!total) return 0;
    return (value / total) * 100;
  }

  ngOnInit(): void {
    this.loadStats();
  }

  loadStats(): void {
    this.firewallService.getDashboardStats().subscribe({
      next: (stats: Statistics) => {
        this.stats = stats;
        if (stats?.by_status) {
          this.totalStatus = Object.values(stats.by_status as Record<string, number>).reduce((sum: number, val: number) => sum + val, 0);
        }
        if (stats?.by_landing_zone) {
          this.totalZone = Object.values(stats.by_landing_zone as Record<string, number>).reduce((sum: number, val: number) => sum + val, 0);
        }
      },
      error: (err: Error) => {
        console.error('Failed to load dashboard stats:', err);
      }
    });
  }
}
