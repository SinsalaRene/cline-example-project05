import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, map } from 'rxjs';
import { User } from '../../shared/interfaces';
export type { User };

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
    public user$ = this.stateSubject.pipe(map((s: AuthState) => s.user));

    login(email: string, password: string): Observable<any> {
        this.stateSubject.next({ ...this.stateSubject.value, loading: true });
        return this.http.post('/api/v1/auth/login', { email, password }).pipe(
            map((res: any) => {
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