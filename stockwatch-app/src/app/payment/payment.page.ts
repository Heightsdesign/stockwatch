import { Component, OnInit } from '@angular/core';
import { ApiService } from '../services/api.service';
import dropin from 'braintree-web-drop-in';

@Component({
  selector: 'app-payment',
  templateUrl: './payment.page.html',
  styleUrls: ['./payment.page.scss'],
})
export class PaymentPage implements OnInit {
  clientToken: string | undefined;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    // Step 1: Get Braintree client token
    this.apiService.getBraintreeClientToken().subscribe((res) => {
      this.clientToken = res.client_token;
      this.initializeBraintreeDropin();
    });
  }
  initializeBraintreeDropin() {
    if (!this.clientToken) return;

    const options = {
      authorization: this.clientToken,
      container: '#dropin-container', // Ensure this exists in your HTML
      paypal: {
        flow: 'vault' // Use 'checkout' for one-time payments or 'vault' for saving PayPal for future use
      }
    };

    dropin.create(options, (createErr: Error | null, instance: any) => {
      if (createErr) {
        console.error('Braintree Drop-in UI creation error:', createErr);
        return;
      }

      if (!instance) {
        console.error('Braintree instance not created');
        return;
      }

      // Add event listener to pay button
      const button = document.querySelector('#submit-button');
      if (button) {
        button.addEventListener('click', () => {
          instance.requestPaymentMethod((err: Error | null, payload: { nonce: string, type: string } | null) => {
            if (err) {
              console.error('Payment method request error:', err);
              return;
            }

            if (!payload) {
              console.error('No payment method payload received');
              return;
            }

            console.log('Selected payment method:', payload.type); // Debug log for payment method type

            // Send nonce to backend for processing
            this.apiService.checkoutBraintree({
              amount: 10, // Replace with actual amount
              payment_method_nonce: payload.nonce
            }).subscribe(
              (response) => {
                console.log('Payment success:', response);
              },
              (error) => {
                console.error('Payment error:', error);
              }
            );
          });
        });
      }
    });
  }
}
