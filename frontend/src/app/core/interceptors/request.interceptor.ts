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