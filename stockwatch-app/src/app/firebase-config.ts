// src/firebase-config.ts
import { initializeApp } from "firebase/app";
import { getMessaging } from "firebase/messaging";

const firebaseConfig = {
  apiKey: "AIzaSyAc2NyN-dnUAViG9AVSDGRgbUgFpbJuv10",
  authDomain: "stockwatch-cd67b.firebaseapp.com",
  projectId: "stockwatch-cd67b",
  storageBucket: "stockwatch-cd67b.firebasestorage.app",
  messagingSenderId: "115008457664",
  appId: "1:115008457664:web:076d7f0c88f9a84d961625",
  measurementId: "G-90LBBWKWY8"
};

const app = initializeApp(firebaseConfig);
export const messaging = getMessaging(app);
