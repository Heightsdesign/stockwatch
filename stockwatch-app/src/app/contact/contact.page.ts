import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ApiService } from '../services/api.service';  // your custom service
import { AlertController } from '@ionic/angular';

@Component({
  selector: 'app-contact',
  templateUrl: './contact.page.html',
  styleUrls: ['./contact.page.scss'],
})
export class ContactPage implements OnInit {
  contactForm!: FormGroup;

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private alertController: AlertController
  ) {}

  ngOnInit() {
    this.contactForm = this.fb.group({
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      message: ['', Validators.required],
    });
  }

  async submitForm() {
    if (this.contactForm.valid) {
      const formValue = this.contactForm.value;
      try {
        // Call an API endpoint that handles contact messages
        await this.apiService.sendContactMessage(formValue);

        // Show success
        const alert = await this.alertController.create({
          header: 'Success',
          message: 'Your message has been sent!',
          buttons: ['OK'],
        });
        await alert.present();

        // Reset the form if needed
        this.contactForm.reset();
      } catch (error) {
        // Show error
        const alert = await this.alertController.create({
          header: 'Error',
          message: 'Failed to send message. Please try again.',
          buttons: ['OK'],
        });
        await alert.present();
      }
    }
  }
}
