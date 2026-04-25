import { Injectable, inject, OnDestroy, OnInit } from '@angular/core';
import { Observable, BehaviorSubject, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { ApiService } from './api.service';
import { User, LoginResponse } from './interfaces';

@Injectable({
    providedIn: 'root'
})
export class AuthService implements OnDestroy {
    private apiService = inject(ApiService);
    private currentUserSubject = new BehaviorSubject<User | null>(this.loadUser());
    public currentUser$ = this.currentUserSubject.asObservable();
    public isLoggedIn$ = this.currentUserSubject.pipe(
        map(user => !!user && user.is_active !== false)
    );
    public roles: string[] = [];

    constructor() {
        // Initialize roles from stored user
        const user = this.loadUser();
        if (user) {
            this.roles = [user.role];
        }
    }

    ngOnDestroy(): void {
        this.currentUserSubject.complete();
    }

    private loadUser(): User | null {
        const data = localStorage.getItem('auth_user');
        return data ? JSON.parse(data) : null;
    }

    login(accessToken: string, userData: User): void {
        localStorage.setItem('access_token', accessToken);
        localStorage.setItem('refresh_token', userData['refresh_token'] || '');
        localStorage.setItem('auth_user', JSON.stringify(userData));
        this.currentUserSubject.next(userData);
        this.roles = [userData.role];
    }

    logout(): void {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('auth_user');
        this.currentUserSubject.next(null);
        this.roles = [];
    }

    getToken(): string | null {
        return localStorage.getItem('access_token');
    }

    isAuthenticated(): boolean {
        const user = this.loadUser();
        return !!user && !!localStorage.getItem('access_token');
    }

    getRole(): string {
        const user = this.loadUser();
        return user?.role || 'anonymous';
    }

    hasRole(roles: string[]): boolean {
        const user = this.loadUser();
        if (!user) {
            return false;
        }
        return roles.includes(user.role);
    }

    getCurrentUser(): Observable<User | null> {
        const stored = this.loadUser();
        return of(stored);
    }

    refreshUser(): Observable<User | null> {
        return new Observable((observer) => {
            const user = this.loadUser();
            if (!user) {
                observer.next(null);
                observer.complete();
                return;
            }
            this.apiService.get<any>('/auth/me').subscribe({
                next: (data) => {
                    localStorage.setItem('auth_user', JSON.stringify(data));
                    this.currentUserSubject.next(data);
                    observer.next(data);
                    observer.complete();
                },
                error: () => {
                    this.logout();
                    observer.next(null);
                    observer.complete();
                }
            });
        });
    }
}