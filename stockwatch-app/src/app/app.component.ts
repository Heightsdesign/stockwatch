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
    const token = await requestNotificationPermission();
    if (token) {
      // Send the token to your backend for user-device mapping
      this.http
        .post('/api/register-device-token/', { token })
        .subscribe(
          () => console.log('Token registered with backend.'),
          (err) => console.error('Error registering token:', err)
        );
    }

    // Start listening for messages
    listenForMessages();
  }
}
