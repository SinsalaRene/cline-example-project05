# Session 4: Frontend Enhancement

## Context

You are working on the Azure Firewall Manager application. Sessions 1-3 (Security, API, Database) have been completed. Now we modernize the Angular frontend with improved architecture, state management, UI/UX, and features.

## Project Structure (After Sessions 1-3)

```
cline-example-project05/
├── backend/                  # Sessions 1-3 completed
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── app.component.ts
│   │   │   ├── app.module.ts
│   │   │   ├── core/              # NEW: Core services & interceptors
│   │   │   │   ├── interceptors/
│   │   │   │   ├── guards/
│   │   │   │   └── models/
│   │   │   ├── shared/
│   │   │   │   ├── services/
│   │   │   │   ├── components/    # NEW: Reusable components
│   │   │   │   ├── pipes/         # NEW: Custom pipes
│   │   │   │   └── directives/    # NEW: Custom directives
│   │   │   └── features/
│   │   │       ├── auth/          # NEW: Auth feature
│   │   │       ├── dashboard/     # NEW: Dashboard feature
│   │   │       ├── rules/
│   │   │       ├── approvals/
│   │   │       └── admin/
│   │   ├── assets/
│   │   └── environments/
│   ├── angular.json
│   ├── package.json
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
└── .env.example
```

## Tasks

### Task 4.1: Update `frontend/package.json`

Add new dependencies:

```json
{
  "dependencies": {
    "@angular/animations": "^17.0.0",
    "@angular/common": "^17.0.0",
    "@angular/compiler": "^17.0.0",
    "@angular/core": "^17.0.0",
    "@angular/forms": "^17.0.0",
    "@angular/platform-browser": "^17.0.0",
    "@angular/platform-browser-dynamic": "^17.0.0",
    "@angular/router": "^17.0.0",
    "@angular/cdk": "^17.0.0",
    "@angular/material": "^17.0.0",
    "@angular/ssr": "^17.0.0",
    
    "rxjs": "~7.8.0",
    "tslib": "^2.3.0",
    "zone.js": "~0.14.0",
    
    "ngx-toastr": "^18.0.0",
    "ngx-spinner": "^16.0.0",
    "@angular-eslint/schematics": "^17.0.0",
    "chart.js": "^4.4.0",
    "ng2-charts": "^5.0.0",
    "@ngx-translate/core": "^14.0.0",
    "@ngx-translate/http-loader": "^7.0.0"
  },
  "devDependencies": {
    "@angular-devkit/build-angular": "^17.0.0",
    "@angular/cli": "^17.0.0",
    "@angular/compiler-cli": "^17.0.0",
    "@types/node": "^20.0.0",
    "typescript": "~5.2.0",
    "jasmine": "^5.1.0",
    "jasmine-core": "^5.1.0",
    "karma": "^6.4.0",
    "karma-chrome-launcher": "^3.2.0",
    "karma-coverage": "^2.2.0",
    "karma-jasmine": "^5.1.0",
    "karma-jasmine-html-reporter": "^2.1.0",
    "eslint": "^8.56.0",
    "@angular-eslint/eslint-plugin": "^17.0.0",
    "@angular-eslint/template-parser": "^17.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "prettier": "^3.0.0"
  }
}
```

### Task 4.2: Core Interceptors (`frontend/src/app/core/interceptors/`)

Create `request.interceptor.ts`:

```typescript
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Injectable, Inject } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable()
export class RequestInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    const token = localStorage.getItem('access_token');
    
    const cloned = req.clone({
      setHeaders: {
        Authorization: token ? `Bearer ${token}` : '',
        'X-Request-ID': this.generateRequestId()
      }
    });
    
    return next.handle(cloned).pipe(
      catchError(error => {
        console.error('HTTP Error:', error);
        return throwError(() => error);
      })
    );
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
  }
}
```

Create `error.interceptor.ts`:

```typescript
import { HttpInterceptor, HttpRequest, HttpHandler, HttpEvent } from '@angular/common/http';
import { Injectable, Inject } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable()
export class ErrorInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
    return next.handle(req).pipe(
      catchError((error) => {
        let errorMessage = 'An unexpected error occurred';
        
        if (error.status === 401) {
          localStorage.removeItem('access_token');
          errorMessage = 'Session expired. Please log in again.';
        } else if (error.status === 403) {
          errorMessage = 'Access denied';
        } else if (error.status === 404) {
          errorMessage = 'Resource not found';
        } else if (error.status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        }
        
        console.error(`Error [${error.status}]:`, errorMessage);
        return throwError(() => new Error(errorMessage));
      })
    );
  }
}
```

### Task 4.3: Auth Guards (`frontend/src/app/core/guards/`)

Create `auth.guard.ts` (enhanced):

```typescript
import { Injectable, inject } from '@angular/core';
import { CanActivateFn, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../shared/auth.service';

export const authGuard: CanActivateFn = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  
  if (authService.isAuthenticated()) {
    return true;
  }
  
  // Save the attempted URL for redirect after login
  localStorage.setItem('redirectUrl', state.url);
  router.navigate(['/login']);
  return false;
};

export const roleGuard: CanActivateFn = (
  route: ActivatedRouteSnapshot,
  state: RouterStateSnapshot
) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  
  const requiredRoles = route.data['roles'] as string[];
  const userRole = authService.getUser()?.role;
  
  if (requiredRoles.includes(userRole)) {
    return true;
  }
  
  router.navigate(['/access-denied']);
  return false;
};
```

### Task 4.4: Auth Service (`frontend/src/app/core/services/auth.service.ts`)

```typescript
import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, map } from 'rxjs';
import { User } from '../interfaces';

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);
  
  private readonly stateSubject = new BehaviorSubject<AuthState>({
    user: null,
    token: localStorage.getItem('access_token'),
    isAuthenticated: !!localStorage.getItem('access_token'),
    loading: false
  });
  
  public state$ = this.stateSubject.asObservable();
  public user$ = this.stateSubject.pipe(map(s => s.user));
  
  login(email: string, password: string): Observable<any> {
    this.stateSubject.next({ ...this.stateSubject.value, loading: true });
    return this.http.post('/api/v1/auth/login', { email, password }).pipe(
      map(res => {
        localStorage.setItem('access_token', res.token);
        localStorage.setItem('refresh_token', res.refresh_token);
        this.stateSubject.next({
          user: res.user,
          token: res.token,
          isAuthenticated: true,
          loading: false
        });
        return res;
      })
    );
  }
  
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.stateSubject.next({
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false
    });
  }
  
  getUser(): User | null {
    return this.stateSubject.value.user;
  }
  
  isAuthenticated(): boolean {
    return this.stateSubject.value.isAuthenticated;
  }
  
  hasRole(role: string): boolean {
    const user = this.stateSubject.value.user;
    return user && user.role === role;
  }
}
```

### Task 4.5: Common Components (`frontend/src/app/shared/components/`)

Create `confirm-dialog.component.ts`:

```typescript
import { Component, inject, input } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';

export interface ConfirmDialogData {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
}

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [MatButtonModule, MatDialogModule, FormsModule],
  template: `
    <h2 mat-dialog-title>{{ data().title }}</h2>
    <mat-dialog-content>
      <p>{{ data().message }}</p>
    </mat-dialog-content>
    <mat-dialog-actions>
      <button mat-button (click)="dialogRef.close(false)">
        {{ data().cancelText || 'Cancel' }}
      </button>
      <button mat-raised-button color="primary" (click)="dialogRef.close(true)">
        {{ data().confirmText || 'Confirm' }}
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    mat-dialog-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
      padding: 8px;
    }
  `]
})
export class ConfirmDialogComponent {
  data = input.required<ConfirmDialogData>();
  dialogRef = inject(MatDialogRef<ConfirmDialogComponent>);
}
```

Create `loading-spinner.component.ts`:

```typescript
import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [MatProgressSpinnerModule],
  template: `
    <div class="loading-overlay" *ngIf="loading">
      <mat-spinner diameter="48"></mat-spinner>
      <p>{{ message }}</p>
    </div>
  `,
  styles: [`
    .loading-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(255,255,255,0.8);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      z-index: 9999;
    }
    mat-spinner { margin-bottom: 16px; }
  `]
})
export class LoadingSpinnerComponent implements OnInit, OnDestroy {
  private authService = inject(AuthService);
  loading = false;
  message = 'Loading...';
  
  ngOnInit(): void {
    this.authService.state$.subscribe(s => {
      this.loading = s.loading;
      this.message = s.loading ? 'Please wait...' : '';
    });
  }
  
  ngOnDestroy(): void {}
}
```

### Task 4.6: Enhanced Rules Component (`frontend/src/app/features/rules/rules.component.ts`)

```typescript
import { Component, OnInit, inject, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, Router } from '@angular/router';
import { FirewallRule, RuleFilter, User } from '../../shared/interfaces';
import { FirewallService } from '../../shared/firewall.service';
import { AuthService } from '../../core/services/auth.service';
import { ConfirmDialogComponent } from '../../shared/components/confirm-dialog.component';

@Component({
  selector: 'app-rules',
  standalone: true,
  imports: [
    CommonModule,
    MatButtonModule,
    MatInputModule,
    MatFormFieldModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatChipsModule
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
              <mat-chip [class]="getStatusColor(rule.status)">
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
  `
})
export class RulesComponent implements OnInit {
  private firewallService = inject(FirewallService);
  private authService = inject(AuthService);
  private router = inject(Router);
  private route = inject(ActivatedRoute);
  private dialog = inject(MatDialog);
  
  rules: FirewallRule[] = [];
  displayedColumns = ['name', 'status', 'action', 'priority', 'actions'];
  dataSource: any;
  filters: RuleFilter = {};
  
  ngOnInit(): void {
    this.loadRules();
  }
  
  loadRules(): void {
    this.firewallService.getRules(this.filters).subscribe({
      next: (data) => {
        this.rules = data.items;
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
      if (confirmed) {
        this.firewallService.deleteRule(rule.id!).subscribe(() => {
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
```

### Task 4.7: Dashboard Component (`frontend/src/app/features/dashboard/`)

Create `dashboard.component.ts`:

```typescript
import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { ChartModule } from 'ng2-charts';
import { ApiService } from '../../shared/api.service';

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
            <div class="stat-value">{{stats?.total_rules || 0}}</div>
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
          <canvas baseChart
            chartType="doughnut"
            [data]="statusChartData"
            [options]="statusChartOptions">
          </canvas>
        </mat-card>
        
        <mat-card>
          <mat-card-header><mat-card-title>By Landing Zone</mat-card-title></mat-card-header>
          <canvas baseChart
            chartType="bar"
            [data]="zoneChartData"
            [options]="zoneChartOptions">
          </canvas>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .dashboard { padding: 24px; }
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
    }
    .charts-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-top: 20px;
    }
  `]
})
export class DashboardComponent implements OnInit {
  private apiService = inject(ApiService);
  
  stats: any = null;
  statusChartOptions = { responsive: true, plugins: { legend: { position: 'bottom' } } };
  zoneChartOptions = { responsive: true, plugins: { legend: { display: false } } };
  statusChartData: any = { labels: [], datasets: [{ data: [], backgroundColor: [] }] };
  zoneChartData: any = { labels: [], datasets: [{ data: [], backgroundColor: [] }] };
  
  ngOnInit(): void {
    this.loadStats();
  }
  
  loadStats(): void {
    this.apiService.get('/stats/dashboard').subscribe({
      next: (stats) => {
        this.stats = stats;
        this.updateCharts(stats);
      }
    });
  }
  
  updateCharts(stats: any): void {
    const statusLabels = Object.keys(stats.by_status || {});
    const statusValues = Object.values(stats.by_status || {}) as number[];
    this.statusChartData = {
      labels: statusLabels,
      datasets: [{ data: statusValues, backgroundColor: ['#4caf50', '#ff9800', '#f44336', '#2196f3'] }]
    };
    
    const zoneLabels = Object.keys(stats.by_landing_zone || {});
    const zoneValues = Object.values(stats.by_landing_zone || {}) as number[];
    this.zoneChartData = {
      labels: zoneLabels,
      datasets: [{ data: zoneValues, backgroundColor: ['#1976d2', '#9c27b0', '#ff5722', '#4caf50'] }]
    };
  }
}
```

### Task 4.8: Update `frontend/src/app/app.module.ts`

```typescript
import { NgModule, inject } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideToastr } from 'ngx-toastr';
import { provideTranslate, TranslateLoader } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// HTTP Interceptors
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { RequestInterceptor } from './core/interceptors/request.interceptor';
import { ErrorInterceptor } from './core/interceptors/error.interceptor';

export function TranslateLoaderFactory(http: any) {
  return new TranslateHttpLoader(http, './assets/i18n/', '.json');
}

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule
  ],
  providers: [
    provideAnimations(),
    provideHttpClient(withInterceptorsFromDi()),
    provideToastr({
      positionClass: 'toast-top-right',
      timeOut: 5000,
      progressBar: true,
    }),
    provideTranslate({
      loader: {
        provide: TranslateLoader,
        useFactory: TranslateLoaderFactory,
        deps: []
      }
    }),
    { provide: HTTP_INTERCEPTORS, useClass: RequestInterceptor, multi: true },
    { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
```

### Task 4.9: Update `frontend/Dockerfile`

```dockerfile
# Build stage
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration production

# Production stage
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Task 4.10: Update `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-XSS-Protection "1; mode=block";
    add_header Cache-Control "no-store, no-cache, must-revalidate";

    # API proxy
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## Testing

```bash
cd frontend
npm install
ng build
ng test --watch=false
```

## Acceptance Criteria

- [ ] Angular Material components are used throughout
- [ ] HTTP interceptors add auth tokens and request IDs
- [ ] Auth guards protect routes
- [ ] Confirm dialog component works for destructive actions
- [ ] Rules component has search and filter
- [ ] Dashboard shows statistics with charts
- [ ] Error interceptor handles 401/403/500 errors
- [ ] Docker build succeeds
- [ ] Responsive layout works on mobile/tablet