importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.22.0/firebase-messaging-compat.js');

firebase.initializeApp({
  apiKey: "AIzaSyAc2NyN-dnUAViG9AVSDGRgbUgFpbJuv10",
  authDomain: "stockwatch-cd67b.firebaseapp.com",
  projectId: "stockwatch-cd67b",
  storageBucket: "stockwatch-cd67b.firebasestorage.app",
  messagingSenderId: "115008457664",
  appId: "1:115008457664:web:076d7f0c88f9a84d961625",
  measurementId: "G-90LBBWKWY8"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage(function(payload) {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/assets/icon/favicon.ico', // Optional: Update the path to your icon
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

