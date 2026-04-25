import { bootstrapApplication } from '@angular/platform-browser';
import { AppComponent } from './app/app.component';
import { provideHttpClient } from '@angular/common/http/http';
import { provideRouter, Routes } from '@angular/router';
import { MAT_DIALOG_DEFAULT_OPTIONS } from '@angular/material/dialog';

const routes: Routes = [
    { path: '', redirectTo: 'login', pathMatch: 'full' },
    { path: 'login', loadComponent: () => import('./app/login/login.component').then(m => m.LoginComponent) },
    {
        path: 'rules',
        loadComponent: () => import('./app/rules/rules.component').then(m => m.RulesComponent)
    },
    {
        path: 'rules/:id',
        loadComponent: () => import('./app/rules/rule-detail/rule-detail.component').then(m => m.RuleDetailComponent)
    },
    {
        path: 'approvals',
        loadComponent: () => import('./app/approvals/approvals.component').then(m => m.ApprovalsComponent)
    },
    { path: '**', redirectTo: 'rules' }
];

bootstrapApplication(AppComponent, {
    providers: [
        provideHttpClient(),
        provideRouter(routes),
        { provide: MAT_DIALOG_DEFAULT_OPTIONS, useValue: { hasBackdrop: true } }
    ]
}).catch(err => console.error(err));