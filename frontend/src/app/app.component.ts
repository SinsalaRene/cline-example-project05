import { Component, OnInit, inject } from '@angular/core';
import { RouterOutlet, Router, NavigationEnd, RouterLink, RouterLinkActive } from '@angular/router';
import { filter } from 'rxjs/operators';
import { NgIf, NgStyle } from '@angular/common';
import { AuthService, User } from './core/services/auth.service';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [RouterOutlet, RouterLink, RouterLinkActive, NgIf],
    template: `
        <div class="app-layout">
            <nav class="sidebar" *ngIf="isLoggedIn">
                <div class="sidebar-brand">
                    <span>FIREWALL</span>
                    <span class="brand-sub">Portal</span>
                </div>
                <ul class="nav-links">
                    <li><a routerLink="/dashboard" routerLinkActive="active">Dashboard</a></li>
                    <li><a routerLink="/rules" routerLinkActive="active">Rules</a></li>
                </ul>
                <div class="sidebar-footer">
                    <div class="user-info">
                        <span class="username">{{userName}}</span>
                        <span class="role-badge">{{role}}</span>
                    </div>
                    <button (click)="logout()" class="btn btn-logout">Logout</button>
                </div>
            </nav>
            <main class="main-content">
                <router-outlet></router-outlet>
            </main>
        </div>
    `,
    styles: [`
        .app-layout {
            display: flex;
            min-height: 100vh;
            font-family: 'Segoe UI', Roboto, sans-serif;
        }
        .sidebar {
            width: 240px;
            background: #1a1a2e;
            color: #fff;
            display: flex;
            flex-direction: column;
            position: fixed;
            top: 0;
            left: 0;
            height: 100vh;
            overflow-y: auto;
        }
        .sidebar-brand {
            padding: 20px;
            display: flex;
            flex-direction: column;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .sidebar-brand span { font-size: 18px; font-weight: 700; }
        .brand-sub { font-size: 12px; opacity: 0.7; font-weight: 400; }
        .nav-links { list-style: none; padding: 0; margin: 20px 0; }
        .nav-links li { margin: 4px 0; }
        .nav-links a {
            display: block;
            padding: 12px 20px;
            color: rgba(255,255,255,0.7);
            text-decoration: none;
            transition: all 0.2s;
        }
        .nav-links a:hover, .nav-links a.active {
            color: #fff;
            background: rgba(255,255,255,0.1);
            border-left: 3px solid #00d4ff;
            padding-left: 17px;
        }
        .sidebar-footer {
            margin-top: auto;
            padding: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
        }
        .user-info { margin-bottom: 12px; }
        .username { display: block; font-size: 13px; }
        .role-badge {
            display: inline-block;
            font-size: 11px;
            padding: 2px 8px;
            background: rgba(0,212,255,0.2);
            color: #00d4ff;
            border-radius: 10px;
            margin-top: 4px;
        }
        .main-content {
            flex: 1;
            margin-left: 240px;
            background: #f5f7fa;
            min-height: 100vh;
        }
        .btn { cursor: pointer; border: none; padding: 8px 16px; border-radius: 4px; font-size: 14px; }
        .btn-logout {
            background: #ff4444;
            color: white;
            width: 100%;
        }
    `])
export class AppComponent implements OnInit {
    title = 'fw-portal';
    isLoggedIn = true;
    userName = 'User';
    role = 'viewer';
    private authService = inject(AuthService);

    user$ = this.authService.user$;

    ngOnInit(): void {
        this.user$.subscribe((user: User | null) => {
            if (user) {
                this.userName = user.display_name;
                this.role = user.role;
                this.isLoggedIn = true;
            } else {
                this.isLoggedIn = false;
            }
        });
    }

    logout(): void {
        this.authService.logout();
        window.location.href = '/login';
    }
}