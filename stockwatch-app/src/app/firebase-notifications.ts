// src/app/firebase-notifications.ts

import { messaging } from './firebase-config';
import { getToken, onMessage } from 'firebase/messaging';

export async function requestNotificationPermission(): Promise<string | null> {
  console.log("Requesting permission for notifications...");
  const permission = await Notification.requestPermission();

  if (permission === "granted") {
    console.log("Notification permission granted.");
    try {
      const token = await getToken(messaging, {
        vapidKey: "BDc2pzDKbbsnytR3IwuQYh_4aZQvWCM7NmMVdRWjyyCjppxH3RVfvfu_p4Wn83PiLM3wDqkARJvebDfGnkNJGOM",
      });
      console.log("FCM registration token:", token);
      return token;
    } catch (error) {
      console.error("Error getting FCM token:", error);
    }
  } else {
    console.warn("Notification permission denied.");
  }
  return null;
}

export function listenForMessages(): void {
  onMessage(messaging, (payload) => {
    console.log("Message received. ", payload);
    const notificationTitle = payload.notification?.title ?? "Default Title";
    const notificationOptions = {
      body: payload.notification?.body ?? "Default body",
      icon: payload.notification?.icon,
    };
    new Notification(notificationTitle, notificationOptions);
  });
}
