import { NgModule, inject } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideHttpClient, withInterceptorsFromDi } from '@angular/common/http';
import { provideToastr } from 'ngx-toastr';
import { provideTranslate, TranslateLoader } from '@ngx-translate/core';
import { TranslateHttpLoader } from '@ngx-translate/http-loader';

import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';

// HTTP Interceptors
import { HTTP_INTERCEPTORS } from '@angular/common/http';
import { RequestInterceptor } from './core/interceptors/request.interceptor';
import { ErrorInterceptor } from './core/interceptors/error.interceptor';

export function TranslateLoaderFactory(http: any) {
    return new TranslateHttpLoader(http, './assets/i18n/', '.json');
}

@NgModule({
    declarations: [
        AppComponent
    ],
    imports: [
        BrowserModule,
        AppRoutingModule
    ],
    providers: [
        provideAnimations(),
        provideHttpClient(withInterceptorsFromDi()),
        provideToastr({
            positionClass: 'toast-top-right',
            timeOut: 5000,
            progressBar: true,
        }),
        provideTranslate({
            loader: {
                provide: TranslateLoader,
                useFactory: TranslateLoaderFactory,
                deps: []
            }
        }),
        { provide: HTTP_INTERCEPTORS, useClass: RequestInterceptor, multi: true },
        { provide: HTTP_INTERCEPTORS, useClass: ErrorInterceptor, multi: true }
    ],
    bootstrap: [AppComponent]
})
export class AppModule { }