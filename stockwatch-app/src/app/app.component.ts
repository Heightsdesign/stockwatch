// src/app/app.component.ts

import { Component, OnInit } from '@angular/core';
import { requestNotificationPermission, listenForMessages } from './firebase-notifications';
import { HttpClient } from '@angular/common/http';
import { v4 as uuidv4 } from 'uuid';
 // After `npm i --save-dev @types/uuid`

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html',
  styleUrls: ['app.component.scss'],
})
export class AppComponent implements OnInit {
  constructor(private http: HttpClient) {}

  async ngOnInit() {
    let device_id = localStorage.getItem('device_id');
    if (!device_id) {
      // If device_id is null, we generate a new one
      const newDeviceId = uuidv4();
      localStorage.setItem('device_id', newDeviceId);
      device_id = newDeviceId;
    }

    const device_token = await requestNotificationPermission();
    if (device_token) {
      this.http.post('http://localhost:8000/creds/register-device-token/', {
        device_id: device_id, // device_id is now guaranteed to be a string
        device_token: device_token
      })
      .subscribe(
        () => console.log('Token registered with backend.'),
        (err) => {
          if (err.status === 200 || err.status === 201) {
            console.log('Token registered (201 Created or 200 OK).');
          } else if (err.status === 400 && err.error && typeof err.error === 'object' && Array.isArray(err.error.device_token)) {
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
