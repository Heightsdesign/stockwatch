// src/app/app.component.ts

import { Component, OnInit } from '@angular/core'; // Import OnInit
import { HttpClient } from '@angular/common/http'; // Import HttpClient
import { requestNotificationPermission, listenForMessages } from './firebase-notifications'; // Import notification functions

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
      // Send the token to your backend
      this.http.post('/api/register-device-token/', { token }).subscribe(
        () => console.log('Token registered with backend.'),
        (err: any) => console.error('Error registering token:', err) // Specify the type for 'err'
      );
    }

    // Start listening for messages
    listenForMessages();
  }
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/firebase-messaging-sw.js')
      .then(registration => {
        console.log('Service Worker registered with scope:', registration.scope);
      })
      .catch(err => {
        console.error('Service Worker registration failed:', err);
      });
  });
}
