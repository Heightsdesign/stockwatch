import { Component } from '@angular/core';
import { ApiService } from '../services/api.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-phone-verification',
  templateUrl: './phone-verification.page.html',
  styleUrls: ['./phone-verification.page.scss'],
})
export class PhoneVerificationPage {
  verificationCode: string = '';
  verificationStatus: string = '';

  constructor(private apiService: ApiService, private router: Router) {}

  verifyPhone() {
    this.apiService.verifyPhone(this.verificationCode).subscribe({
      next: () => {
        this.verificationStatus = 'Your phone number has been successfully verified.';
        setTimeout(() => this.router.navigate(['/dashboard']), 3000); // Redirect after 3 seconds
      },
      error: () => {
        this.verificationStatus = 'Verification failed. Please check your code and try again.';
      },
    });
  }
}
