import { messaging } from './firebase-config';
import { getToken, onMessage } from 'firebase/messaging';

// Request permission and get FCM token
export async function requestNotificationPermission() {
  try {
    const token = await getToken(messaging, {
      vapidKey: 'BDc2pzDKbbsnytR3IwuQYh_4aZQvWCM7NmMVdRWjyyCjppxH3RVfvfu_p4Wn83PiLM3wDqkARJvebDfGnkNJGOM', // Replace with your Firebase VAPID key
    });
    console.log('FCM Token:', token);
    return token;
  } catch (err) {
    console.error('Error getting FCM token:', err);
    return null;
  }
}

// Listen for incoming FCM messages
export function listenForMessages() {
  onMessage(messaging, (payload) => {
    console.log('Message received:', payload);
  });
}
