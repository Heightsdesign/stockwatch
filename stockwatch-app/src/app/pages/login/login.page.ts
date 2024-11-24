// src/app/pages/login/login.page.ts

import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { LoadingController, AlertController } from '@ionic/angular';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.page.html',
  styleUrls: ['./login.page.scss'],
})
export class LoginPage implements OnInit {
  loginForm!: FormGroup;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private loadingController: LoadingController,
    private alertController: AlertController,
    private router: Router
  ) { }

  ngOnInit() {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]]
    });
  }

  async onLogin() {
    const loading = await this.loadingController.create({
      message: 'Logging in...',
    });
    await loading.present();

    this.apiService.login(this.loginForm.value).subscribe(
      async (res) => {
        await loading.dismiss();
        // Handle successful login
        // Save the token and navigate to the home page
        console.log('Login response:', res);
        localStorage.setItem('auth_token', res.token);
        this.router.navigate(['/home']);
      },
      async (err) => {
        await loading.dismiss();
        const alert = await this.alertController.create({
          header: 'Login Failed',
          message: 'Invalid email or password.',
          buttons: ['OK']
        });
        await alert.present();
      }
    );
  }
}
