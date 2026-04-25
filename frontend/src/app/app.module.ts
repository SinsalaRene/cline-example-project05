import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';

import { AppComponent } from './app.component';
import { LoginComponent } from './login/login.component';
import { RulesComponent } from './rules/rules.component';
import { RuleDetailComponent } from './rules/rule-detail/rule-detail.component';
import { ApprovalsComponent } from './approvals/approvals.component';

@NgModule({
    declarations: [
        AppComponent,
        LoginComponent,
        RulesComponent,
        RuleDetailComponent,
        ApprovalsComponent
    ],
    imports: [
        BrowserModule,
        FormsModule,
        ReactiveFormsModule,
        HttpClientModule
    ],
    providers: [],
    bootstrap: [AppComponent]
})
export class AppModule { }