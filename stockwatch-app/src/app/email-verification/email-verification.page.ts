import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { ApiService } from '../services/api.service';

@Component({
  selector: 'app-email-verification',
  templateUrl: './email-verification.page.html',
  styleUrls: ['./email-verification.page.scss'],
})
export class EmailVerificationPage implements OnInit {
  verificationStatus: string = ''; // To show success or error message

  constructor(
    private route: ActivatedRoute,
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    const uid = this.route.snapshot.paramMap.get('uid');
    const token = this.route.snapshot.paramMap.get('token');

    if (uid && token) {
      this.verifyEmail(uid, token);
    } else {
      this.verificationStatus = 'Invalid verification link.';
    }
  }

  verifyEmail(uid: string, token: string) {
    this.apiService.verifyEmail(uid, token).subscribe({
      next: () => {
        this.verificationStatus = 'Your email has been successfully verified.';
        setTimeout(() => this.router.navigate(['/login']), 3000); // Redirect after 3 seconds
      },
      error: () => {
        this.verificationStatus = 'Verification failed. Please try again.';
      },
    });
  }
}
