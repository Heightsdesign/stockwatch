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
  intercept(
    req: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    // Retrieve the token from localStorage
    const token = localStorage.getItem('auth_token');
    console.log('AuthInterceptor - Token:', token);

    // Clone the request to add the new header
    if (token) {
      const cloned = req.clone({
        headers: req.headers.set('Authorization', `Token ${token}`),
      });
      console.log('AuthInterceptor - Cloned Request with Auth:', cloned);
      // Pass the cloned request instead of the original request to the next handle
      return next.handle(cloned);
    } else {
      console.log('AuthInterceptor - No token found');
      // If no token, pass the original request
      return next.handle(req);
    }
  }
}
