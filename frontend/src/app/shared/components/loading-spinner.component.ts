import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../core/services/auth.service';

@Component({
    selector: 'app-loading-spinner',
    standalone: true,
    imports: [MatProgressSpinnerModule, CommonModule],
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

    ngOnDestroy(): void { }
}