import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../shared/auth.service';

@Component({
    selector: 'app-login',
    template: `
        <div class="login-container">
            <div class="login-card">
                <h2>Firewall Portal</h2>
                <p class="subtitle">Azure Firewall Rule Management Platform</p>
                <div class="form-group">
                    <label>Email</label>
                    <input type="email" [(ngModel)]="email" placeholder="admin@example.com" />
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" [(ngModel)]="password" placeholder="Password (dev: any)" />
                </div>
                <div *ngIf="error" style="color:red; margin-bottom:16px;">{{ error }}</div>
                <button (click)="onLogin()" class="btn-login">Sign in</button>
                <p style="margin-top:16px; font-size:12px; color:#888; text-align:center;">
                    Demo: admin@example.com / any password
                </p>
            </div>
        </div>
    `,
    styles: [`
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        .login-card {
            background: #fff;
            border-radius: 12px;
            padding: 40px;
            width: 400px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .login-card h2 {
            text-align: center;
            margin-bottom: 8px;
            color: #333;
        }
        .login-card .subtitle {
            text-align: center;
            color: #888;
            margin-bottom: 32px;
            font-size: 14px;
        }
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            margin-bottom: 4px;
            font-weight: 500;
            font-size: 14px;
            color: #555;
        }
        .form-group input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        .btn-login {
            width: 100%;
            padding: 12px;
            background: #007bff;
            color: #fff;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            cursor: pointer;
            font-weight: 600;
            margin-top: 8px;
        }
        .btn-login:hover { background: #0056b3; }
    `])
export class LoginComponent {
    email = 'admin@example.com';
    password = '';
    error = '';

    private authService = inject(AuthService);
    private router = inject(Router);

    onLogin(): void {
        // In production, this would redirect to Azure login
        // For dev, create mock user
        const mockUser = {
            id: 1,
            email: this.email,
            display_name: this.email.split('@')[0],
            role: this.email.includes('admin') ? 'admin' :
                this.email.includes('security') ? 'security_stakeholder' :
                    this.email.includes('workload') ? 'workload_stakeholder' : 'viewer',
            workload: 'default',
            is_active: true
        };
        this.authService.login('mock-token-' + Date.now(), mockUser);
        this.router.navigate(['/rules']);
    }
}