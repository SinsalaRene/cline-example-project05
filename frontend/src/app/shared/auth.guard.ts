import { Injectable, inject } from '@angular/core';
import { CanActivate, Router, UrlTree, ActivatedRouteSnapshot, RouterStateSnapshot, UrlSegment } from '@angular/router';
import { Observable, from, of } from 'rxjs';
import { catchError, map, tap } from 'rxjs/operators';
import { AuthService } from './auth.service';
import { ApiService } from './api.service';

@Injectable({
    providedIn: 'root'
})
export class AuthGuard implements CanActivate {
    private authService = inject(AuthService);
    private router = inject(Router);
    private apiService = inject(ApiService);

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Observable<boolean | UrlTree> {
        if (this.authService.isAuthenticated()) {
            return of(true);
        }
        return from(this.refreshAuth()).pipe(
            map((isValid: boolean) => {
                if (isValid) {
                    return true;
                }
                return this.router.createUrlTree(['/login'], {
                    queryParams: { returnUrl: state.url }
                });
            }),
            catchError(() => {
                this.authService.logout();
                return of(this.router.createUrlTree(['/login'], {
                    queryParams: { returnUrl: state.url }
                }));
            })
        );
    }

    private refreshAuth(): Promise<boolean> {
        return new Promise((resolve) => {
            const token = this.authService.getToken();
            if (!token) {
                resolve(false);
                return;
            }
            this.apiService.get<any>('/auth/me').subscribe({
                next: () => resolve(true),
                error: () => resolve(false)
            });
        });
    }
}