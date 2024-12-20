// src/app/interceptors/auth.interceptor.ts

import { Injectable } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
} from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  // Define the list of URLs that should exclude the Authorization header
  private excludedUrls: string[] = [
    '/creds/registration/',
    '/creds/api-token-auth/',
    // Add any other public endpoints here
  ];

  intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    // Check if the request URL matches any of the excluded URLs
    const isExcluded = this.excludedUrls.some(url => req.url.includes(url));

    if (isExcluded) {
      // If the URL is excluded, forward the request without modifying headers
      console.log(`AuthInterceptor - Excluding URL: ${req.url}`);
      return next.handle(req);
    }

    // Retrieve the token from localStorage
    const token = localStorage.getItem('auth_token');
    console.log('AuthInterceptor - Token:', token);

    if (token) {
      // Clone the request and add the Authorization header
      const cloned = req.clone({
        headers: req.headers.set('Authorization', `Token ${token}`),
      });
      console.log('AuthInterceptor - Cloned Request with Auth:', cloned);
      return next.handle(cloned);
    } else {
      console.log('AuthInterceptor - No token found');
      // If no token, forward the original request
      return next.handle(req);
    }
  }
}
