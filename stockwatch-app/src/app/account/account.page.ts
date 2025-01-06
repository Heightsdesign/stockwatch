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
    // NEW: We assume the backend returns is_phone_verified for phone verification status
    is_phone_verified: false,
  };

  countries: any[] = [];
  selectedCountry: any;
  phonePrefix: string = '';

  showPushToggle = false;
  notificationMessage: string = '';
  userHasDeviceToken = false; // To track if user already has a device token

  editMode = false; // from your previous addition

  constructor(private apiService: ApiService, private alertController: AlertController) {}

  ngOnInit() {
    this.loadUserProfile();
    this.loadCountries();
    this.checkNotificationSupport();
  }

  toggleEditMode() {
    this.editMode = !this.editMode;
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
          this.showPushToggle = true;
        } else if (permission === 'denied') {
          this.showPushToggle = false;
          this.notificationMessage = 'Push notifications are blocked. Enable them in your browser settings.';
        }
      }
    } else if (this.isMobileAppPlatform()) {
      console.log("[DEBUG] Mobile platform, enabling push toggle by default.");
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

    if (this.user.receive_push_notifications && (!this.showPushToggle || !this.userHasDeviceToken)) {
      console.log("[DEBUG] User wants push but cannot enable (no toggle or no token). Disabling push.");
      await this.showAlert("Push notifications are currently not available. Please ensure notifications are enabled at app startup.");
      this.user.receive_push_notifications = false;
    }

    // Actually save
    this.saveUserProfile();
    this.editMode = false;
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
    if (!phoneNumberDigits.startsWith(prefixDigits)) {
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
      // e.g. data might contain is_phone_verified
      // this.user.is_phone_verified = data.is_phone_verified || false;

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
    this.apiService.getUserDevices().subscribe(
      (devices: any[]) => {
        if (devices && devices.length > 0) {
          console.log("[DEBUG] User has devices:", devices);
          this.userHasDeviceToken = true;
        } else {
          console.log("[DEBUG] User has no device token registered.");
          this.userHasDeviceToken = false;
          if (this.user.receive_push_notifications) {
            this.user.receive_push_notifications = false;
            this.showAlert("No device token found. Push notifications require enabling notifications at app startup.");
          }
        }
      },
      (error) => {
        console.error("[DEBUG] Failed to load user devices", error);
        this.userHasDeviceToken = false;
        if (this.user.receive_push_notifications) {
          this.user.receive_push_notifications = false;
          this.showAlert("Could not verify device token. Push notifications disabled.");
        }
      }
    );
  }

  // NEW/UPDATED: Called whenever user toggles SMS on/off
  async onToggleSMSNotifications(event: any) {
    // user.receive_sms_notifications is already changed at this point
    const turnedOn = this.user.receive_sms_notifications;

    // 1. If toggling ON, ensure a phone number is present
    if (turnedOn) {
      // If no phone number, disallow
      if (!this.user.phone_number) {
        await this.showErrorAlert("Please enter a phone number before enabling SMS notifications.");
        // revert
        this.user.receive_sms_notifications = false;
        return;
      }
      // If phone is not verified, send code automatically & prompt user
      if (!this.user.is_phone_verified) {
        // Call an API to send the code or rely on server logic
        // For minimal approach, assume your server does it if you do `updateUserProfile()`
        // or you have an endpoint like "resendPhoneVerification()"
        this.sendVerificationCode();
      }
      // If phone is already verified, do nothing special
    } else {
      // Toggling off -> we do nothing special
      console.log("[DEBUG] SMS notifications turned OFF.");
    }
  }

  // NEW: Send code if user toggles SMS on but phone is not verified
  async sendVerificationCode() {
    try {
      // Suppose you have an endpoint like 'resendPhoneVerification' or 'sendPhoneVerification'
      // Or you can simply call updateUserProfile, but that might alter other fields
      // We'll assume you have something like:
      await this.apiService.resendPhoneVerification().toPromise();
      // Then prompt user for code
      this.promptForVerificationCode();
    } catch (err) {
      console.error("[DEBUG] Failed to send verification code automatically", err);
      this.user.receive_sms_notifications = false;
      this.showErrorAlert("Failed to send verification code. Please try again.");
    }
  }

  // NEW: Prompt user to enter code
  async promptForVerificationCode() {
    const alert = await this.alertController.create({
      header: 'Enter Verification Code',
      inputs: [
        {
          name: 'code',
          type: 'text',
          placeholder: '6-digit code'
        }
      ],
      buttons: [
        {
          text: 'Cancel',
          role: 'cancel',
          handler: () => {
            // user canceled verifying, let's revert the toggle
            this.user.receive_sms_notifications = false;
          }
        },
        {
          text: 'Verify',
          handler: (data) => {
            if (!data.code || data.code.length !== 6) {
              this.showErrorAlert("Invalid verification code format.");
              // keep toggled on for the moment or revert it?
              // We can choose to revert:
              this.user.receive_sms_notifications = false;
              return;
            }
            this.verifyPhone(data.code);
          }
        }
      ]
    });
    await alert.present();
  }

  // NEW: Verify code with your phone verification endpoint
  async verifyPhone(code: string) {
    this.apiService.verifyPhone(code).subscribe(
      async (res: any) => {
        // success
        this.user.is_phone_verified = true;
        // phone is verified, user can keep SMS on
        const alert = await this.alertController.create({
          header: 'Success',
          message: 'Phone number verified successfully.',
          buttons: ['OK']
        });
        await alert.present();
      },
      async (err) => {
        // fail
        this.user.receive_sms_notifications = false;
        const alert = await this.alertController.create({
          header: 'Verification Failed',
          message: 'Invalid or expired verification code. SMS notifications turned off.',
          buttons: ['OK']
        });
        await alert.present();
      }
    );
  }
}
