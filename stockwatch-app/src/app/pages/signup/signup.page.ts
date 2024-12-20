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

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private loadingController: LoadingController,
    private alertController: AlertController,
    private router: Router
  ) {}

  ngOnInit() {
    this.signupForm = this.fb.group({
      username: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      password1: ['', [Validators.required, Validators.minLength(8)]],
      password2: ['', [Validators.required]],
    });
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

    const loading = await this.loadingController.create({
      message: 'Signing up...',
    });
    await loading.present();

    // Call the API service
    this.apiService.signup(this.signupForm.value).subscribe(
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

        // Handle error response
        let errorMessage = 'An error occurred. Please try again later.';
        if (err.error) {
          if (err.error.username) {
            errorMessage = err.error.username.join(' ');
          } else if (err.error.email) {
            errorMessage = err.error.email.join(' ');
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
