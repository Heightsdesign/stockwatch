import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { LoadingController, AlertController } from '@ionic/angular';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-signup',
  templateUrl: './signup.page.html',
  styleUrls: ['./signup.page.scss'],
})
export class SignupPage implements OnInit {
  signupForm!: FormGroup;
  countries: { name: string; iso_code: string; phone_prefix: string }[] = [];
  selectedCountry?: { name: string; iso_code: string; phone_prefix: string };
  phonePrefix: string = '';

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private loadingController: LoadingController,
    private alertController: AlertController,
    private router: Router
  ) {}

  ngOnInit() {
    this.initializeForm();
    this.loadCountries();
  }

  initializeForm() {
    this.signupForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      country: ['', [Validators.required]],
      phone_number: [
        '',
        [
          Validators.pattern(/^\+?[1-9]\d{1,14}$/), // E.164 international phone number format
        ],
      ],
      password1: ['', [Validators.required, Validators.minLength(8)]],
      password2: ['', [Validators.required]],
    });

    // Watch for changes in the country field to update the phone prefix
    this.signupForm.get('country')?.valueChanges.subscribe((iso_code) => {
      this.updatePhonePrefix(iso_code);
    });
  }

  async loadCountries() {
    try {
      const loading = await this.loadingController.create({
        message: 'Loading countries...',
      });
      await loading.present();

      this.apiService.getCountries().subscribe(
        (data: any[]) => {
          this.countries = data.map((country) => ({
            name: country.name,
            iso_code: country.iso_code,
            phone_prefix: country.phone_prefix,
          }));
          loading.dismiss();
        },
        async (error) => {
          loading.dismiss();
          console.error('Failed to load countries', error);
          const alert = await this.alertController.create({
            header: 'Error',
            message: 'Failed to load countries. Please try again later.',
            buttons: ['OK'],
          });
          await alert.present();
        }
      );
    } catch (error) {
      console.error('Unexpected error while loading countries', error);
    }
  }

  updatePhonePrefix(iso_code: string) {
    const country = this.countries.find((c) => c.iso_code === iso_code);
    if (country) {
      this.selectedCountry = country;
      this.phonePrefix = country.phone_prefix;
      console.log('[DEBUG] Country selected:', country.name, 'Prefix:', this.phonePrefix);
      // Optionally, reset the phone number field when country changes
      this.signupForm.get('phone_number')?.reset();
    } else {
      this.selectedCountry = undefined;
      this.phonePrefix = '';
    }
  }

  async onSignup() {
    // Check for password mismatch
    if (this.signupForm.value.password1 !== this.signupForm.value.password2) {
      const alert = await this.alertController.create({
        header: 'Password Mismatch',
        message: 'Passwords do not match. Please try again.',
        buttons: ['OK'],
      });
      await alert.present();
      return;
    }

    // Ensure country is selected before proceeding (redundant due to validators but added for extra safety)
    if (!this.selectedCountry) {
      const alert = await this.alertController.create({
        header: 'Country Not Selected',
        message: 'Please select a country before entering your phone number.',
        buttons: ['OK'],
      });
      await alert.present();
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Signing up...',
    });
    await loading.present();

    // Prepare the payload
    const payload = {
      username: this.signupForm.value.username,
      email: this.signupForm.value.email,
      phone_number: this.signupForm.value.phone_number,
      country: this.signupForm.value.country,
      password1: this.signupForm.value.password1,
      password2: this.signupForm.value.password2,
    };

    // Call the API service
    this.apiService.signup(payload).subscribe(
      async (res) => {
        await loading.dismiss();

        const alert = await this.alertController.create({
          header: 'Registration Successful',
          message: 'Your account has been created. Please log in.',
          buttons: ['OK'],
        });
        await alert.present();

        // Redirect to login page
        this.router.navigate(['/login']);
      },
      async (err) => {
        await loading.dismiss();

        if (err.status === 429) {

          const alert = await this.alertController.create({
            header: 'Too Many Attempts',
            message:
              err.error.error ||
              'You have made too many verification attempts. Please wait 2 minutes before trying again.',
            buttons: ['OK'],
          });
          await alert.present();
          return;
        }

        // Handle error response
        let errorMessage = 'An error occurred. Please try again later.';
        if (err.error) {
          if (err.error.username) {
            errorMessage = err.error.username.join(' ');
          } else if (err.error.email) {
            errorMessage = err.error.email.join(' ');
          } else if (err.error.phone_number) {
            errorMessage = err.error.phone_number.join(' ');
          } else if (err.error.password1) {
            errorMessage = err.error.password1.join(' ');
          } else if (err.error.non_field_errors) {
            errorMessage = err.error.non_field_errors.join(' ');
          }
        }

        const alert = await this.alertController.create({
          header: 'Registration Failed',
          message: errorMessage,
          buttons: ['OK'],
        });
        await alert.present();
      }
    );
  }
}
