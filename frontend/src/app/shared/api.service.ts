import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams, HttpHeaders } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';
import { ApiResponse, User } from './interfaces';

@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private http = inject(HttpClient);
    baseUrl = environment.apiUrl;

    private getToken(): string | null {
        return localStorage.getItem('access_token');
    }

    private getHeaders(): HttpHeaders {
        const token = this.getToken();
        return new HttpHeaders({
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        });
    }

    get<T>(endpoint: string, params?: Record<string, string>): Observable<T> {
        let httpParams = new HttpParams();
        if (params) {
            Object.entries(params).forEach(([key, value]) => {
                if (value !== undefined && value !== null) {
                    httpParams = httpParams.append(key, String(value));
                }
            });
        }
        return this.http.get<T>(`${this.baseUrl}${endpoint}`, {
            headers: this.getHeaders(),
            params: httpParams
        }).pipe(catchError(this.handleError));
    }

    post<T>(endpoint: string, body: unknown): Observable<T> {
        return this.http.post<T>(`${this.baseUrl}${endpoint}`, body, {
            headers: this.getHeaders()
        }).pipe(catchError(this.handleError));
    }

    put<T>(endpoint: string, body: unknown): Observable<T> {
        return this.http.put<T>(`${this.baseUrl}${endpoint}`, body, {
            headers: this.getHeaders()
        }).pipe(catchError(this.handleError));
    }

    delete<T>(endpoint: string): Observable<T> {
        return this.http.delete<T>(`${this.baseUrl}${endpoint}`, {
            headers: this.getHeaders()
        }).pipe(catchError(this.handleError));
    }

    patch<T>(endpoint: string, body: unknown): Observable<T> {
        return this.http.patch<T>(`${this.baseUrl}${endpoint}`, body, {
            headers: this.getHeaders()
        }).pipe(catchError(this.handleError));
    }

    private handleError(error: Error): Observable<never> {
        console.error('API Error:', error);
        return throwError(() => error);
    }
}