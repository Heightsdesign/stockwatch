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
      username: ['', [Validators.required]],
      email: ['', [Validators.required, Validators.email]],
      password1: ['', [Validators.required]],
      password2: ['', [Validators.required]],
    });
  }

  async onSignup() {
    if (this.signupForm.value.password1 !== this.signupForm.value.password2) {
      const alert = await this.alertController.create({
        header: 'Password Mismatch',
        message: 'Passwords do not match.',
        buttons: ['OK'],
      });
      await alert.present();
      return;
    }

    const loading = await this.loadingController.create({
      message: 'Signing up...',
    });
    await loading.present();

    this.apiService.signup(this.signupForm.value).subscribe(
      async (res) => {
        await loading.dismiss();
        // Optionally, log the user in automatically after registration
        // localStorage.setItem('token', res.token);
        // this.router.navigate(['/home']);

        // Or navigate to login page
        const alert = await this.alertController.create({
          header: 'Registration Successful',
          message: 'Your account has been created. Please log in.',
          buttons: ['OK'],
        });
        await alert.present();
        this.router.navigate(['/login']);
      },
      async (err) => {
        await loading.dismiss();
        const alert = await this.alertController.create({
          header: 'Registration Failed',
          message: 'An error occurred during registration.',
          buttons: ['OK'],
        });
        await alert.present();
      }
    );
  }
}
