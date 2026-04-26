import { Injectable, inject } from '@angular/core';
import { CanActivateFn, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';

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