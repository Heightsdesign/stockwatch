// src/app/app.module.ts

import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouteReuseStrategy } from '@angular/router';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { AuthInterceptor } from './services/auth.interceptor';
import { IonicModule, IonicRouteStrategy } from '@ionic/angular';

import { AppComponent } from './app.component';
import { AppRoutingModule } from './app-routing.module';
import { SharedModule } from './shared/shared.module'; // Import the shared module
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const firebaseConfig = {
  apiKey: "AIzaSyAc2NyN-dnUAViG9AVSDGRgbUgFpbJuv10",
  authDomain: "stockwatch-cd67b.firebaseapp.com",
  projectId: "stockwatch-cd67b",
  storageBucket: "stockwatch-cd67b.firebasestorage.app",
  messagingSenderId: "115008457664",
  appId: "1:115008457664:web:076d7f0c88f9a84d961625",
  measurementId: "G-90LBBWKWY8"
}

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

@NgModule({
  declarations: [AppComponent],
  imports: [
    BrowserModule,
    IonicModule.forRoot(),
    AppRoutingModule,
    HttpClientModule,
    SharedModule // Include SharedModule here
  ],
  providers: [
    { provide: RouteReuseStrategy, useClass: IonicRouteStrategy },
    { provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }
  ],
  bootstrap: [AppComponent]
})
export class AppModule {}
