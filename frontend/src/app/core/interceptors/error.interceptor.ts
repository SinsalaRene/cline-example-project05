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