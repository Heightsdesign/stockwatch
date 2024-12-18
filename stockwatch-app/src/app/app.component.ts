// src/app/app.component.ts

import { Component, OnInit } from '@angular/core';
import {
  requestNotificationPermission,
  listenForMessages,
} from './firebase-notifications';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
})
export class AppComponent implements OnInit {
  constructor(private http: HttpClient) {}

  async ngOnInit() {
    const device_token = await requestNotificationPermission();
    if (device_token) {
      // Send the token to your backend for user-device mapping
      // app.component.ts snippet
      this.http.post('http://localhost:8000/creds/register-device-token/', { device_token: device_token })
        .subscribe(
          () => console.log('Token registered with backend.'),
          (err) => {
            if (err.status === 200 || err.status === 201) {
              // Token accepted
              console.log('Token registered (201 Created or 200 OK).');
            } else if (err.status === 400 && err.error && err.error.device_token && Array.isArray(err.error.device_token)) {
              // If the error says device token already exists
              const errors = err.error.device_token;
              if (errors.some((msg: string) => msg.includes('already exists'))) {
                console.log('Device token already registered, no action needed.');
              } else {
                console.error('Error registering token:', err);
              }
            } else {
              console.error('Error registering token:', err);
            }
          }
        );

    }

    // Start listening for messages
    listenForMessages();
  }
}
