import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';
import { AlertController } from '@ionic/angular';

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
    receive_push_notifications: false,
  };

  countries: any[] = [];
  selectedCountry: any;
  phonePrefix: string = '';

  showPushToggle = false;
  notificationMessage: string = '';
  userHasDeviceToken = false; // To track if user already has a device token

  constructor(private apiService: ApiService, private alertController: AlertController) {}

  ngOnInit() {
    this.loadUserProfile();
    this.loadCountries();
    this.checkNotificationSupport();
  }

  checkNotificationSupport() {
    if (this.isBrowserPlatform()) {
      const permission = Notification.permission;
      console.log("[DEBUG] Current notification permission:", permission);
      if (!('Notification' in window)) {
        this.showPushToggle = false;
        this.notificationMessage = 'Push notifications are not supported by your browser.';
      } else {
        if (permission === 'granted') {
          this.showPushToggle = true;
        } else if (permission === 'default') {
          // User never granted/denied explicitly, we can show toggle but actual enabling depends on token
          this.showPushToggle = true;
        } else if (permission === 'denied') {
          this.showPushToggle = false;
          this.notificationMessage = 'Push notifications are blocked. Enable them in your browser settings.';
        }
      }
    } else if (this.isMobileAppPlatform()) {
      console.log("[DEBUG] Mobile platform, enabling push toggle by default.");
      // On a mobile app platform, assume we can show push toggle and native code will handle permissions
      this.showPushToggle = true;
    } else {
      console.log("[DEBUG] Not browser or mobile platform, disabling push toggle.");
      this.showPushToggle = false;
      this.notificationMessage = 'Push notifications are not available on this platform.';
    }
  }

  isBrowserPlatform(): boolean {
    return typeof window !== 'undefined' && !!window.document;
  }

  isMobileAppPlatform(): boolean {
    // Adjust if needed for a mobile native setup
    return false;
  }

  updatePhonePrefix() {
    if (this.selectedCountry) {
      this.phonePrefix = this.selectedCountry.phone_prefix;
      this.user.country = this.selectedCountry.iso_code;
      console.log("[DEBUG] Country selected:", this.user.country, "Prefix:", this.phonePrefix);
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
    this.checkNotificationSupport();

    console.log("[DEBUG] Before saving profile. showPushToggle:", this.showPushToggle, "User wants push?", this.user.receive_push_notifications);

    // If user wants push but no toggle visible or no token, cannot enable push
    if (this.user.receive_push_notifications && (!this.showPushToggle || !this.userHasDeviceToken)) {
      console.log("[DEBUG] User wants push but cannot enable (no toggle or no token). Disabling push.");
      await this.showAlert("Push notifications are currently not available. Please ensure notifications are enabled at app startup.");
      this.user.receive_push_notifications = false;
    }

    // Directly save the profile now
    this.saveUserProfile();
  }

  saveUserProfile() {
    const selectedCountry = this.countries.find(
      (country) => country.iso_code === this.user.country
    );

    if (!selectedCountry) {
      console.log("[DEBUG] No valid country selected.");
      this.showErrorAlert("Please select a valid country.");
      return;
    }

    let phoneNumberDigits = this.user.phone_number.replace(/\D/g, '');
    if (!phoneNumberDigits) {
      console.log("[DEBUG] No valid phone number digits.");
      this.showErrorAlert("Please enter a valid phone number.");
      return;
    }

    const prefixDigits = selectedCountry.phone_prefix.replace(/\D/g, '');
    // If user already included prefix
    if (phoneNumberDigits.startsWith(prefixDigits)) {
      console.log("[DEBUG] User included prefix already, not adding again.");
      // do nothing extra
    } else {
      phoneNumberDigits = prefixDigits + phoneNumberDigits;
    }

    const fullPhoneNumber = `+${phoneNumberDigits}`;
    this.user.phone_number = fullPhoneNumber;
    console.log("[DEBUG] Final phone number:", fullPhoneNumber);

    this.apiService.updateUserProfile(this.user).subscribe(
      () => {
        console.log('User profile updated successfully');
        this.showSuccessAlert("Your profile has been updated successfully.");
      },
      (error: any) => {
        console.error('Failed to update user profile', error);
        console.log("Full error object: ", error);

        if (error.status === 400 && error.error && typeof error.error === 'object') {
          const errorMessages = [];
          for (const key in error.error) {
            if (error.error.hasOwnProperty(key)) {
              const fieldErrors = error.error[key];
              if (Array.isArray(fieldErrors)) {
                errorMessages.push(...fieldErrors);
              }
            }
          }
          const combinedErrorMessage = errorMessages.join(' ');
          this.showErrorAlert(combinedErrorMessage || "An unexpected error occurred.");
        } else {
          this.showErrorAlert("An error occurred while updating your profile. Please try again.");
        }
      }
    );
  }

  loadUserProfile() {
    this.apiService.getUserProfile().subscribe((data) => {
      this.user = data;
      this.checkNotificationSupport();
      this.loadUserDevices(); // Load devices after loading profile
    });
  }

  loadCountries() {
    this.apiService.getCountries().subscribe((data) => {
      this.countries = data;
      if (this.user.country) {
        this.selectedCountry = this.countries.find(
          (c) => c.iso_code === this.user.country
        );
        if (this.selectedCountry) {
          this.phonePrefix = this.selectedCountry.phone_prefix;
          console.log("[DEBUG] After countries load, user country:", this.user.country, "Prefix:", this.phonePrefix);
        }
      }
    });
  }

  loadUserDevices() {
    // This method must be implemented in your ApiService
    // It should return the list of user devices (with tokens).
    this.apiService.getUserDevices().subscribe((devices: any[]) => {
      if (devices && devices.length > 0) {
        console.log("[DEBUG] User has devices:", devices);
        this.userHasDeviceToken = true;
      } else {
        console.log("[DEBUG] User has no device token registered.");
        this.userHasDeviceToken = false;
        // If user tries to enable push while no token is present, we show a message in updateUserProfile()
      }

      // If userHasDeviceToken is false and user wants push, we handle that in updateUserProfile()
      // If userHasDeviceToken is true and showPushToggle is true, user can set push on
      if (!this.userHasDeviceToken) {
        // Maybe show a placeholder message if user tries to enable push
        if (this.user.receive_push_notifications) {
          this.user.receive_push_notifications = false;
          this.showAlert("No device token found. Push notifications require enabling notifications at app startup.");
        }
      }
    }, (error) => {
      console.error("[DEBUG] Failed to load user devices", error);
      // If we can't load devices, assume none
      this.userHasDeviceToken = false;
      if (this.user.receive_push_notifications) {
        this.user.receive_push_notifications = false;
        this.showAlert("Could not verify device token. Push notifications disabled.");
      }
    });
  }
}
