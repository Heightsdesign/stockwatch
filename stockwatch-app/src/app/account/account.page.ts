import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';
import { AlertController } from '@ionic/angular';
// Import permission checking logic
import { requestNotificationPermission } from '../firebase-notifications';

@Component({
  selector: 'app-account',
  templateUrl: './account.page.html',
  styleUrls: ['./account.page.scss'],
})

export class AccountPage implements OnInit {
  user = {
    username: '',
    email: '',
    phone_number: '',
    country: '',
    receive_email_notifications: true,
    receive_sms_notifications: true,
    receive_push_notifications: false, // default false
  };

  countries: any[] = [];
  selectedCountry: any;
  phonePrefix: string = '';

  // A property to control visibility of the push toggle on web
  showPushToggle = false;
  // A message to display if notifications are blocked or unsupported
  notificationMessage: string = '';

  constructor(private apiService: ApiService, private alertController: AlertController) {}

  ngOnInit() {
    this.loadUserProfile();
    this.loadCountries();
    this.checkNotificationSupport();
  }

  checkNotificationSupport() {
    if (this.isBrowserPlatform()) {
      if (!('Notification' in window)) {
        // Browser does not support notifications
        this.showPushToggle = false;
        this.notificationMessage = 'Your browser does not support push notifications.';
      } else {
        // Check permission
        const permission = Notification.permission;
        if (permission === 'granted') {
          this.showPushToggle = true;
        } else if (permission === 'default') {
          // User has not granted/denied yet, we can show toggle and request when turned on
          this.showPushToggle = true;
        } else if (permission === 'denied') {
          // Notifications blocked
          this.showPushToggle = false;
          this.notificationMessage = 'Notifications are blocked in your browser settings. Enable them to use push notifications.';
        }
      }
    } else if (this.isMobileAppPlatform()) {
      // If mobile app, assume we can show the toggle and handle permissions natively
      this.showPushToggle = true;
    } else {
      // If neither web nor mobile app is detected, default to no push
      this.showPushToggle = false;
    }
  }

  // Helper functions
  isBrowserPlatform(): boolean {
    return typeof window !== 'undefined' && !!window.document;
  }

  isMobileAppPlatform(): boolean {
    // If using Capacitor or another mobile platform detection:
    // return Capacitor.isNativePlatform();
    return false; // Adjust if needed
  }

  updatePhonePrefix() {
    if (this.selectedCountry) {
      this.phonePrefix = this.selectedCountry.phone_prefix;
      // We no longer set user.phone_number here to avoid double prefix issues.
      this.user.country = this.selectedCountry.iso_code;
    }
  }

  async showAlert(message: string) {
    const alert = await this.alertController.create({
      header: 'Notification',
      message: message,
      buttons: ['OK']
    });
    await alert.present();
  }

  async showErrorAlert(message: string) {
    const alert = await this.alertController.create({
      header: 'Error',
      message: message,
      buttons: ['OK']
    });
    await alert.present();
  }

  async showSuccessAlert(message: string) {
    const alert = await this.alertController.create({
      header: 'Success',
      message: message,
      buttons: ['OK']
    });
    await alert.present();
  }

  async updateUserProfile() {
    // If push toggle is not visible or user turned it off, just save profile
    if (!this.showPushToggle || !this.user.receive_push_notifications) {
      this.saveUserProfile();
      return;
    }

    // If push is on and we are on web platform with default permission,
    // request permission now
    if (this.isBrowserPlatform()) {
      const permission = Notification.permission;
      if (permission === 'default') {
        const token = await requestNotificationPermission();
        if (!token) {
          // Permission denied
          alert('You have denied push notifications. Please enable them in browser settings if you want push notifications.');
          this.user.receive_push_notifications = false;
        } else {
          // Register token
          await this.registerDeviceToken(token);
        }
      } else if (permission === 'granted') {
        // Already granted, attempt to get token
        const token = await requestNotificationPermission();
        if (token) await this.registerDeviceToken(token);
      } else if (permission === 'denied') {
        alert('Push notifications are blocked. Please enable them in your browser settings.');
        this.user.receive_push_notifications = false;
      }
    } else if (this.isMobileAppPlatform()) {
      // On mobile, request permissions natively if needed
      // If denied, show message and set receive_push_notifications = false
      // If granted, get token and register it
    }

    // After handling token or denial, save profile anyway
    this.saveUserProfile();
  }

  saveUserProfile() {
    // Format phone number
    const selectedCountry = this.countries.find(
      (country) => country.iso_code === this.user.country
    );
    if (!selectedCountry) {
      this.showErrorAlert("Please select a country.");
      return;
    }

    const phoneNumberDigits = this.user.phone_number.replace(/\D/g, '');
    if (!phoneNumberDigits) {
      this.showErrorAlert("Please enter a valid phone number.");
      return;
    }
    const fullPhoneNumber = `${selectedCountry.phone_prefix}${phoneNumberDigits}`;
    this.user.phone_number = fullPhoneNumber;

    this.apiService.updateUserProfile(this.user).subscribe(
      () => {
        console.log('User profile updated successfully');
        this.showSuccessAlert("Your profile has been updated successfully.");
      },
      (error: any) => {
        console.error('Failed to update user profile', error);
        console.log("Full error object: ", error);

        // Check if we have a known error structure
        if (error.status === 400 && error.error && typeof error.error === 'object') {
          // For example, if the error is like { phone_number: ["The phone number entered is not valid."] }
          // we can extract that message.
          const errorMessages = [];

          // Iterate over the error object keys
          for (const key in error.error) {
            if (error.error.hasOwnProperty(key)) {
              const fieldErrors = error.error[key];
              // fieldErrors is likely an array of strings
              if (Array.isArray(fieldErrors)) {
                errorMessages.push(...fieldErrors);
              }
            }
          }

          // Join all error messages, or just take the first if you prefer
          const combinedErrorMessage = errorMessages.join(' ');
          this.showErrorAlert(combinedErrorMessage || "An unexpected error occurred.");
        } else {
          // If we cannot parse a specific message, revert to generic
          this.showErrorAlert("An error occurred while updating your profile. Please try again.");
        }
      }
    );
  }


  loadUserProfile() {
    this.apiService.getUserProfile().subscribe((data) => {
      this.user = data;
      this.checkNotificationSupport();
    });
  }

  loadCountries() {
    this.apiService.getCountries().subscribe((data) => {
      this.countries = data;
      // If user already has a country set, let's find it
      if (this.user.country) {
        this.selectedCountry = this.countries.find(
          (c) => c.iso_code === this.user.country
        );
        if (this.selectedCountry) {
          this.phonePrefix = this.selectedCountry.phone_prefix;
        }
      }
    });
  }

  registerDeviceToken(token: string) {
    return new Promise<void>((resolve, reject) => {
      this.apiService.registerDeviceToken({ device_token: token }).subscribe(
        () => {
          console.log('Device token registered successfully');
          resolve();
        },
        (error) => {
          console.error('Failed to register device token', error);
          this.user.receive_push_notifications = false;
          resolve();
        }
      );
    });
  }
}
