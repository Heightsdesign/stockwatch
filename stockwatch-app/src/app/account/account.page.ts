import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';

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
    receive_push_notifications: true,
  };

  countries: any[] = [];
  selectedCountry: any;
  phonePrefix: string = '';

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadUserProfile();
    this.loadCountries();
  }

  loadUserProfile() {
    this.apiService.getUserProfile().subscribe((data) => {
      this.user = data;
    });
  }

  loadCountries() {
    this.apiService.getCountries().subscribe((data) => {
      this.countries = data;
    });
  }

  updatePhonePrefix() {
      this.phonePrefix = this.selectedCountry.phone_prefix;
      this.user.phone_number = this.phonePrefix; // Initialize phone number with the prefix
  }

  updateUserProfile() {
    // Format phone number with country code
    const selectedCountry = this.countries.find(
      (country) => country.iso_code === this.user.country
    );

    if (selectedCountry) {
      const phoneNumberDigits = this.user.phone_number.replace(/\D/g, '');
      if (!phoneNumberDigits) {
        alert('Please enter a valid phone number.');
        return;
      }
      const fullPhoneNumber = `${selectedCountry.phone_prefix}${phoneNumberDigits}`;
      this.user.phone_number = fullPhoneNumber;
    } else {
      alert('Please select a country.');
      return;
    }

    this.apiService.updateUserProfile(this.user).subscribe(
      () => console.log('User profile updated successfully'),
      (error) => console.error('Failed to update user profile', error)
    );
  }
}
